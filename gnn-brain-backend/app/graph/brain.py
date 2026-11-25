"""Query routing and grounding on the school's reporting graph."""

import re
from collections import defaultdict
from dataclasses import asdict

import networkx as nx

from app.graph.data import LINKS, NODES, SECTIONS, SUBJECTS
from app.graph.gnn_model import GNN, words
from app.graph.knowledge import SCHOOL_RECORDS, SCHOOL_SCENARIOS

GREETING = re.compile(r"^(?:hi|hey|hello|good (?:morning|afternoon|evening))[! .]*$", re.I)
IDENTITY = re.compile(r"^(?:who are you|tell me about yourself|introduce yourself)[?.! ]*$", re.I)
EVENT = re.compile(r"\b(events?|fest|celebration|function)\b")
GENERIC_EVENT_WORDS = {
    "which", "the", "an", "a", "is", "when", "where", "what", "date", "time", "for",
    "in", "on", "our", "college", "school", "campus", "respective", "this", "that",
    "event", "events", "fest", "function", "celebration", "tell", "me", "about",
}
FOLLOW_UP = re.compile(
    r"^(?:(?:and )?(?:when|where|what time)(?: is (?:it|that)| does it start)?|"
    r"what about (?:the )?(?:time|venue|location|date)|(?:what(?:'s| is) the )?(?:time|venue|location|date))[?! .]*$"
)
SECTION = re.compile(r"\b(?:class|section) ([a-e])\b")
WEAK_ALIASES = {"absences", "absent", "coding", "lab", "essay"}


def normalized(text):
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold().replace("’", "'").replace("'", "")))


TOPIC_ALIASES = {(record.topic, normalized(alias)) for record in SCHOOL_RECORDS for alias in record.aliases}


def matching_topics(question):
    padded = f" {normalized(question)} "
    matches = {(topic, alias) for topic, alias in TOPIC_ALIASES if f" {alias} " in padded}
    specific = {(topic, alias) for topic, alias in matches if alias not in WEAK_ALIASES}
    matches = specific or matches
    # Prefer specific phrases over a generic alias contained inside them.
    return {topic for topic, phrase in matches
            if not any(f" {phrase} " in f" {other} " and phrase != other for _, other in matches)}


class ChatbotEngine:
    def __init__(self):
        self.node_metadata = {node.id: node for node in NODES}
        self.G = nx.DiGraph()
        self.G.add_nodes_from(self.node_metadata)
        self.G.add_edges_from(LINKS)
        if not nx.is_directed_acyclic_graph(self.G):
            raise ValueError("Reporting lines must form a directed acyclic graph.")
        self.records = defaultdict(dict)
        for record in SCHOOL_RECORDS:
            self.records[record.owner][record.topic] = record
        self.gnn = GNN(self.G, self.node_metadata)

    def resolve(self, value):
        if value in self.node_metadata:
            return value
        if value:
            matches = [node.id for node in NODES if node.label.casefold() == value.casefold()]
            if len(matches) == 1:
                return matches[0]
        return None

    def graph_data(self):
        return {
            "nodes": [asdict(node) for node in NODES],
            "links": [{"source": source, "target": target} for source, target in self.G.edges],
            "classes": [{"id": section, "label": f"Class {section}",
                         "studentCount": sum(node.section == section and node.roll is not None for node in NODES)}
                        for section in SECTIONS],
            "subjects": [{"id": subject.key, "label": subject.label} for subject in SUBJECTS],
            "scenarios": SCHOOL_SCENARIOS,
            "defaultNode": "S-A-1",
            "demo": True,
        }

    def chat(self, sender_node_label_or_id, message, previous_question=None):
        start = self.resolve(sender_node_label_or_id or "S-A-1")
        if start is None:
            raise KeyError(sender_node_label_or_id)
        node = self.node_metadata[start]
        text = normalized(message)
        context = message
        if GREETING.fullmatch(message) or IDENTITY.fullmatch(message):
            return self.result(
                f"I’m {node.label}. {node.text} Ask me about a school notice, class activity, or policy.",
                "local", [start], start,
            )

        if text in {"who is my cr", "who is my class representative"} and node.role == "Student":
            representative = self.node_metadata[next(self.G.successors(start))]
            return self.result(f"{representative.label} is the Class {node.section} representative.",
                               "local", [start], start)

        if previous_question and FOLLOW_UP.fullmatch(message.casefold()):
            context = previous_question
            message = f"{previous_question} {message}"
            text = normalized(message)

        mentioned_sections = {section.upper() for section in SECTION.findall(message.casefold())}
        if node.section and mentioned_sections - {node.section}:
            return self.result(
                f"This conversation follows Class {node.section}’s reporting chain. "
                "Choose someone from the other class to ask about their notices.", "clarify", [start],
            )

        topics = matching_topics(message)
        if len(topics) > 1:
            return self.result("I found several topics in that question. Which one should I check first?",
                               "clarify", [start])
        if not topics and EVENT.search(text) and words(text) <= GENERIC_EVENT_WORDS:
            return self.result("Which event do you mean? Share its name, such as Founders Day.",
                               "clarify", [start])

        topic = next(iter(topics), None)
        if topic == "student-profile" and node.roll is None:
            return self.result("Choose a student or class representative to ask about their own projects and interests.",
                               "clarify", [start])
        route = [start]
        current = start
        while True:
            record = self.records.get(current, {}).get(topic)
            if record is not None and (not record.local_only or current == start):
                return self.result(record.answer, "answered", route, current, record, context)
            parents = tuple(self.G.successors(current))
            if not parents:
                break
            current = parents[0] if len(parents) == 1 else self.gnn.choose(message, parents)
            route.append(current)

        if topic:
            section = node.section or (next(iter(mentioned_sections)) if len(mentioned_sections) == 1 else None)
            accessible = self.G.to_undirected(as_view=True).subgraph(
                item.id for item in self.node_metadata.values() if item.section is None or item.section == section
            )
            paths = nx.single_source_shortest_path(accessible, start)
            options = [(paths[record.owner], record) for record in SCHOOL_RECORDS
                       if record.topic == topic and record.owner in paths and not record.local_only
                       and (record.section is None or record.section == section)]
            if options:
                authority_route, record = min(options, key=lambda option: len(option[0]))
                return self.result(record.answer, "answered", authority_route, record.owner, record, context)

        return self.result(
            "I checked the reporting chain and couldn’t find a published answer. "
            "Share the exact notice name or ask the relevant school office to confirm.",
            "unresolved", route,
        )

    @staticmethod
    def result(answer, status, route, source=None, record=None, context=None):
        return {
            "answer": answer,
            "status": status,
            "context": context,
            "sources": [source] if source else [],
            "route": [
                {"node": node_id, "status": (
                    "answered" if node_id == source else "forwarded" if index < len(route) - 1 else "unresolved"
                )}
                for index, node_id in enumerate(route)
            ] if status in {"answered", "unresolved"} else [],
            "returnPath": list(reversed(route)) if record else [],
            "record": {"title": record.title, "reference": record.reference, "node": source} if record else None,
        }


bot_engine = ChatbotEngine()
