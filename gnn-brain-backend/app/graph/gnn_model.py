"""A supervised graph-convolution ranker for the CR's reporting branches."""

import re

import numpy as np

from app.graph.data import DEFAULT_SUBJECT, GENERAL_EXAMPLES, SUBJECTS


def words(text):
    normalized = re.sub(r"\bp\.\s*e\b\.?", "pe", text.casefold())
    return set(re.findall(r"[a-z0-9]+", normalized))


class GNN:
    def __init__(self, graph, nodes):
        self.nodes = nodes
        self.parents = {node_id: tuple(graph.successors(node_id)) for node_id in graph}
        self.staff = tuple(node.id for node in nodes.values() if node.subject)
        self.positions = {node_id: index for index, node_id in enumerate(self.staff)}
        self.vocabulary = {subject.key: words(subject.vocabulary) for subject in SUBJECTS}
        self.propagation = np.eye(len(self.staff))
        for node_id, row in self.positions.items():
            neighbors = [self.positions[parent] for parent in self.parents[node_id] if parent in self.positions]
            self.propagation[row, neighbors] = 1
        self.propagation /= self.propagation.sum(axis=1, keepdims=True)

        branches = self.parents["CR-A"]
        examples = [(example, subject.key) for subject in SUBJECTS for example in subject.examples]
        examples.extend((example, DEFAULT_SUBJECT.key) for example in GENERAL_EXAMPLES)
        features = []
        targets = []
        for question, subject in examples:
            features.extend(self.features(question, branches))
            targets.extend(float(nodes[branch].subject == subject) for branch in branches)
        design = np.asarray(features)
        self.weights = np.linalg.solve(design.T @ design + 0.2 * np.eye(design.shape[1]), design.T @ targets)

    def features(self, question, branches):
        terms = words(question)
        matches = np.array([
            len(terms & (self.vocabulary[node.subject] if node.role == "HOD" else words(node.text)))
            for node in (self.nodes[node_id] for node_id in self.staff)
        ], dtype=float)
        # Each in-charge receives the subject signal from their directly connected HOD.
        convolved = self.propagation @ matches
        general = not any(terms & vocabulary for vocabulary in self.vocabulary.values())
        return np.array([
            (convolved[self.positions[branch]], float(general and self.nodes[branch].subject == DEFAULT_SUBJECT.key))
            for branch in branches
        ])

    def choose(self, question, branches):
        scores = self.features(question, branches) @ self.weights
        index = int(np.argmax(scores))
        return branches[index]
