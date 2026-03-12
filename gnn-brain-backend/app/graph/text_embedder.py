from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class TextEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=32,
            stop_words="english"
        )
        self.node_texts = {}

    def update_node_text(self, node_id: str, text: str):
        self.node_texts.setdefault(node_id, [])
        self.node_texts[node_id].append(text)

    def build_embeddings(self, node_ids):
        corpus = []
        for nid in node_ids:
            texts = self.node_texts.get(nid, [])
            corpus.append(" ".join(texts) if texts else "")

        if not any(corpus):
            # no text yet → return zeros
            return np.zeros((len(node_ids), 32))

        X = self.vectorizer.fit_transform(corpus)
        return X.toarray()
