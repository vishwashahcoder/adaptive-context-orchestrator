class PromptBuilder:

    def build(self, query, scored_memories):

        context = "\n\n".join([
            m["memory"]["content"]
            for m in scored_memories[:5]
        ])

        prompt = f"""
You are an intelligent AI assistant.

Relevant Context:
{context}

User Query:
{query}

Answer carefully using ONLY the context above.
"""

        return prompt