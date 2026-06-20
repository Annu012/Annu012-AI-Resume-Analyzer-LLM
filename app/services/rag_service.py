"""
RAG-style grounding for the job description — pure Python, no external
ML dependencies (no scikit-learn / numpy / FAISS required).

For a demo/local-first setup we avoid a heavyweight vector DB and instead:
  1. Chunk the job description into ~sentence-level pieces.
  2. Score each chunk's relevance to the resume via TF-IDF + cosine
     similarity, implemented from scratch with the standard library.
  3. Retrieve the chunks most relevant to the resume text.

This keeps the "retrieval -> grounded context -> LLM" pipeline shape intact
while keeping installation friction-free on any machine/Python version.
Swap `TfidfRetriever` for a FAISS + embedding-model retriever in production
(see services/llm_service.py for where the LLM provider plugs in).
"""
import math
import re
from collections import Counter
from typing import List

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z+#.]{1,}")


def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def _chunk_text(text: str, max_words: int = 60) -> List[str]:
    """Splits text into rough chunks of ~max_words for retrieval granularity."""
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    chunks, current, word_count = [], [], 0

    for sentence in sentences:
        words = sentence.split()
        if word_count + len(words) > max_words and current:
            chunks.append(" ".join(current))
            current, word_count = [], 0
        current.append(sentence)
        word_count += len(words)

    if current:
        chunks.append(" ".join(current))

    return [c.strip() for c in chunks if c.strip()]


def _term_freq_vector(tokens: List[str]) -> Counter:
    return Counter(tokens)


def _cosine_similarity(vec_a: Counter, vec_b: Counter) -> float:
    if not vec_a or not vec_b:
        return 0.0
    shared = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in shared)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class TfidfRetriever:
    """Minimal local retriever standing in for a vector DB (e.g. FAISS)."""

    def __init__(self, job_description: str, chunk_size: int = 60):
        self.chunks = _chunk_text(job_description, max_words=chunk_size) or [job_description]

        tokenized_chunks = [_tokenize(c) for c in self.chunks]
        doc_count = len(tokenized_chunks)

        # document frequency per term, for IDF weighting
        df = Counter()
        for tokens in tokenized_chunks:
            for term in set(tokens):
                df[term] += 1

        def idf(term: str) -> float:
            return math.log((1 + doc_count) / (1 + df[term])) + 1

        self._idf = idf
        self._chunk_vectors = []
        for tokens in tokenized_chunks:
            tf = _term_freq_vector(tokens)
            weighted = Counter({term: count * idf(term) for term, count in tf.items()})
            self._chunk_vectors.append(weighted)

    def retrieve(self, query_text: str, top_k: int = 3) -> List[str]:
        """Returns the top_k JD chunks most relevant to the query (resume text)."""
        query_tokens = _tokenize(query_text)
        query_tf = _term_freq_vector(query_tokens)
        query_vec = Counter({term: count * self._idf(term) for term, count in query_tf.items()})

        scored = [
            (_cosine_similarity(query_vec, chunk_vec), idx)
            for idx, chunk_vec in enumerate(self._chunk_vectors)
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        top_indices = [idx for _, idx in scored[:top_k]]
        return [self.chunks[i] for i in top_indices]


def build_grounded_context(job_description: str, resume_text: str, top_k: int = 3) -> str:
    """
    Retrieves the JD chunks most relevant to the resume and returns them
    joined as a single grounding context string to feed the LLM prompt.
    """
    retriever = TfidfRetriever(job_description)
    relevant_chunks = retriever.retrieve(resume_text, top_k=top_k)
    return "\n---\n".join(relevant_chunks)
