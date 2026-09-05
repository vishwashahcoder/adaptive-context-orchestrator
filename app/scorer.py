import time
import math
from config import (
    SCORER_SIMILARITY_WEIGHT,
    SCORER_IMPORTANCE_WEIGHT,
    SCORER_RECENCY_WEIGHT,
    SCORER_RECENCY_HALF_LIFE_HOURS
)


class Scorer:

    def score(self, retrieval_results):
        scored = []

        for item in retrieval_results:
            memory = item["memory"]
            
            similarity = item.get("combined_score", 0.0)

            age_hours = max(0.0, (time.time() - memory["timestamp"]) / 3600.0)

            # Compute true exponential time-decay: e^(-ln(2) * age / half_life)
            half_life = SCORER_RECENCY_HALF_LIFE_HOURS
            recency_score = math.exp(-math.log(2) * (age_hours / half_life))

            final_score = (
                SCORER_SIMILARITY_WEIGHT * similarity +
                SCORER_IMPORTANCE_WEIGHT * memory["importance"] +
                SCORER_RECENCY_WEIGHT * recency_score
            )

            scored.append({
                "memory": memory,
                "score": final_score,
                "breakdown": {
                    "similarity": similarity,
                    "importance": memory["importance"],
                    "recency": recency_score
                }
            })

        scored.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return scored