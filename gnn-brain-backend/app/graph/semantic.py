"""Rank school knowledge by meaning and spelling similarity."""

import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from threading import Thread

import numpy as np

from app.graph.knowledge import SCHOOL_RECORDS

# Example requests supplement the notices with the language a student might use.
PARAPHRASES = {
    "reporting-line": ("who do i report to", "who is directly above me", "who supervises me",
                       "who should i go to first", "who is my immediate supervisor"),
    "founders-day": ("when is the school anniversary celebration", "the big annual celebration date"),
    "student-id": ("cant find my badge", "my identification card went missing", "need a new student card"),
    "leave-request": ("i feel sick and wont be coming in", "not coming in today who should i tell",
                      "need a day off how do i tell them"),
    "missed-exam": ("i couldnt take the test can i sit it later", "missed a paper can i take it another day"),
    "library-hours": ("when can i go to the library", "is the library available after school"),
    "library-loans": ("can i take a book home", "how long can i keep the book", "i need more time to return my book"),
    "class-notes": ("what did we cover while i was away", "need to catch up on what we did"),
    "portal-password": ("locked out of my school account", "cant get into my account"),
    "early-pickup": ("my parent needs to collect me before school ends",),
    "classroom-equipment": ("nothing is coming up on the classroom display",),
    "field-trip": ("who should get the signed form for the museum outing",),
}
STOP = set("a an the is was are were i my we our you your it can could would should do does did to of on in and for me what when where how who please need have get want at be been if about tell with".split())


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower().replace("’", "").replace("'", ""))) - STOP


class KnowledgeIndex:
    def __init__(self):
        examples = defaultdict(set)
        for record in SCHOOL_RECORDS:
            samples = [record.title, *record.aliases, *PARAPHRASES.get(record.topic, ())]
            if record.example:
                samples.append(record.example)
            for sample in samples:
                cleaned = re.sub(r"^(?:Class [A-E]|.+’s student profile)\s*", "", sample)
                if tokens(cleaned):
                    examples[record.topic].add(cleaned)
        examples["reporting-line"].update(PARAPHRASES["reporting-line"])
        self.examples = [(key, sample, tokens(sample)) for key, values in examples.items() for sample in sorted(values)]
        self.vocabulary = sorted(set().union(*(terms for _, _, terms in self.examples)))
        self.encoder = None
        self.vectors = None

    def warm(self):
        """Reuse the project's cached encoder without downloading weights during chat."""
        cache = Path.home() / ".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots"
        if cache.is_dir():
            Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            from sentence_transformers import SentenceTransformer

            encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True, device="cpu")
            vectors = encoder.encode([sample for _, sample, _ in self.examples], normalize_embeddings=True)
            self.encoder, self.vectors = encoder, vectors
        except (ImportError, OSError, RuntimeError):
            pass

    def rank(self, query, allowed=None):
        query_words = tokens(query)
        if not query_words:
            return []
        scores = defaultdict(float)
        # Character similarity handles common misspellings and transpositions in short queries.
        corrected = {}
        for word in query_words:
            if word not in self.vocabulary and len(word) >= 2:
                closest = max(self.vocabulary, key=lambda term: SequenceMatcher(None, word, term).ratio())
                threshold = .8 if len(word) < 4 else .72
                if SequenceMatcher(None, word, closest).ratio() >= threshold:
                    corrected[word] = closest
        query_words = {corrected.get(word, word) for word in query_words}
        dense = self.encoder.encode(query, normalize_embeddings=True) @ self.vectors.T if self.vectors is not None else None
        for index, (topic, _, terms) in enumerate(self.examples):
            if allowed is not None and topic not in allowed:
                continue
            common = len(query_words & terms)
            lexical = common / np.sqrt(len(query_words) * len(terms))
            if common == 1 and len(query_words) >= 3:
                lexical *= .68
            semantic = max(0, float(dense[index]) - .22) * 1.44 if dense is not None else 0
            scores[topic] = max(scores[topic], lexical, semantic)
        return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


knowledge_index = KnowledgeIndex()
