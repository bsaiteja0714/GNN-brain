"""Query routing and grounding on the school's reporting graph."""

import re
from collections import defaultdict
from dataclasses import asdict

import networkx as nx

from app.graph.data import LINKS, NODES, SECTIONS, SUBJECTS
from app.graph.conversation import classify, social_reply, without_lead_in
from app.graph.gnn_model import GNN, words
from app.graph.knowledge import SCHOOL_RECORDS, SCHOOL_SCENARIOS
from app.graph.semantic import knowledge_index

IDENTITY = re.compile(r"^(?:who are you|tell me about yourself|introduce yourself)[?.! ]*$", re.I)
EVENT = re.compile(r"\b(events?|fest|celebration|function)\b")
EVENT_LIST = re.compile(r"\b(?:what|which|list|show|any|upcoming)\b.*\bevents\b|^events$")
EVENT_TOPICS = ("field-trip", "sports-day", "science-fair", "founders-day", "debate-tryouts")
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

    def node_context(self, start):
        node = self.node_metadata[start]
        return {**asdict(node), "reportsTo": [asdict(self.node_metadata[parent]) for parent in self.G.successors(start)]}

    def chat(self, sender_node_label_or_id, message, previous_question=None, has_history=False,
             *, topic_hint=None, institutional=False):
        start = self.resolve(sender_node_label_or_id or "S-A-1")
        if start is None:
            raise KeyError(sender_node_label_or_id)
        node = self.node_metadata[start]
        message = without_lead_in(message)
        text = normalized(message)
        context = message
        lookup_text = message
        if IDENTITY.fullmatch(message):
            return self.result(
                f"I’m {node.label}. {node.text} Ask me about a school notice, class activity, or policy.",
                "local", [start], start,
            )

        if text in {"who is my cr", "who is my class representative"} and node.role == "Student":
            representative = self.node_metadata[next(self.G.successors(start))]
            return self.result(f"{representative.label} is the Class {node.section} representative.",
                               "local", [start], start)

        topics = {topic_hint} if topic_hint else matching_topics(message)
        intent = classify(message, matched=bool(topics), previous_graph=bool(previous_question))
        social = social_reply(intent, name=node.label, has_history=has_history or bool(previous_question))
        if social:
            return self.result(social, "local", [start])
        if not topics and EVENT_LIST.search(text):
            notices = [self.chat(start, message, topic_hint=topic) for topic in EVENT_TOPICS]
            published = [notice for notice in notices if notice["record"]]
            if published:
                answer = "I found these event notices:\n\n" + "\n\n".join(
                    notice["answer"] for notice in published
                )
                return self.result(answer, "local", [start], context=message)
        if previous_question and not topics and FOLLOW_UP.fullmatch(message.casefold()):
            context = previous_question
            lookup_text = previous_question
            message = f"{previous_question} {message}"
            text = normalized(message)
            topics = matching_topics(message)

        if not topics and EVENT.search(text) and words(text) <= GENERIC_EVENT_WORDS:
            return self.result("Which event do you mean? Share its name, such as Founders Day.",
                               "clarify", [start])
        if not topics and not institutional:
            candidates = knowledge_index.rank(lookup_text)
            if candidates:
                top, score = candidates[0]
                margin = score - (candidates[1][1] if len(candidates) > 1 else 0)
                if score >= .56 and margin >= .075:
                    topics = {top}
                elif score >= .56 and len(candidates) > 1:
                    options = [
                        next(record.title for record in SCHOOL_RECORDS
                             if record.topic == key and record.section in {None, node.section})
                        for key, _ in candidates[:2]
                        if any(record.topic == key and record.section in {None, node.section} for record in SCHOOL_RECORDS)
                    ]
                    if len(options) == 2:
                        return self.result(f"Are you asking about {options[0].lower()} or {options[1].lower()}?",
                                           "clarify", [start])
        if not topics and not institutional and intent in {"general", "clarify"}:
            if len(words(text)) <= 3 or intent == "clarify":
                return self.result("What would you like to find out?", "clarify", [start])
            return self.result(f"I don’t have enough information to answer “{message}” from {node.label}’s school records.",
                               "unresolved", [])

        mentioned_sections = {section.upper() for section in SECTION.findall(message.casefold())}
        if node.section and mentioned_sections - {node.section}:
            return self.result(
                f"This conversation follows Class {node.section}’s reporting chain. "
                "Choose someone from the other class to ask about their notices.", "clarify", [start],
            )

        if len(topics) > 1:
            return self.result("I found several topics in that question. Which one should I check first?",
                               "clarify", [start])
        topic = next(iter(topics), None)
        if topic == "reporting-line":
            parents = [f"{parent['label']} ({parent['role']})" for parent in self.node_context(start)["reportsTo"]]
            answer = f"{node.label} reports to {', '.join(parents)}." if parents else f"{node.label} is at the top of this reporting hierarchy."
            return self.result(answer, "local", [start], context=context)
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

        endpoint = self.node_metadata[route[-1]].label
        return self.result(f"I couldn’t find a published answer for “{context}” in the records from {node.label} through {endpoint}.",
                           "unresolved", route, context=context)

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
