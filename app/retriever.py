from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np
from config import SENTENCE_TRANSFORMER_MODEL, RETRIEVER_SEMANTIC_WEIGHT, RETRIEVER_BM25_WEIGHT


class Retriever:

    def __init__(self):
        self.model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)

    def semantic_search(
        self,
        query,
        memories
    ):
        # Encode only the query
        query_embedding = self.model.encode([query])[0]

        # Extract pre-computed embeddings
        memory_embeddings = np.array([
            m["embedding"] for m in memories
        ])

        # Compute cosine similarity: (A . B) / (||A|| * ||B||)
        dot_product = np.dot(memory_embeddings, query_embedding)
        norm_query = np.linalg.norm(query_embedding)
        norm_memories = np.linalg.norm(memory_embeddings, axis=1)
        
        similarities = dot_product / (norm_query * norm_memories + 1e-9)

        return similarities

    def bm25_search(
        self,
        query,
        memories
    ):
        tokenized_memories = [
            m["content"].lower().split()
            for m in memories
        ]

        bm25 = BM25Okapi(tokenized_memories)
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)

        # Normalize BM25 scores to [0, 1] range
        max_score = np.max(scores) if len(scores) > 0 else 0
        min_score = np.min(scores) if len(scores) > 0 else 0
        if max_score > min_score:
            normalized_scores = (scores - min_score) / (max_score - min_score)
        elif max_score > 0:
            normalized_scores = np.ones_like(scores)
        else:
            normalized_scores = np.zeros_like(scores)

        return normalized_scores

    def retrieve(
        self,
        query,
        memories,
        top_k=5
    ):
        if not memories:
            return []

        semantic_scores = self.semantic_search(
            query,
            memories
        )

        bm25_scores = self.bm25_search(
            query,
            memories
        )

        combined_results = []

        for idx, memory in enumerate(memories):
            memory_clean = {k: v for k, v in memory.items() if k != "embedding"}

            semantic_score = float(semantic_scores[idx])
            bm25_score = float(bm25_scores[idx])

            # Stage 1: Hybrid Recall Score
            combined_score = (
                RETRIEVER_SEMANTIC_WEIGHT * semantic_score
                + RETRIEVER_BM25_WEIGHT * bm25_score
            )

            combined_results.append({
                "memory": memory_clean,
                "semantic_score": semantic_score,
                "bm25_score": bm25_score,
                "combined_score": combined_score
            })

        # Sort candidates by Stage 1 score
        combined_results.sort(
            key=lambda x: x["combined_score"],
            reverse=True
        )

        # Stage 2: Precision Candidate Selection (Top 15 candidates for Scorer)
        candidates = combined_results[:15]
        return candidates[:top_k]