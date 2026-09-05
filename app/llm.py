import json
import logging
from PIL import Image
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

class GeminiLLM:

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.default_model = GEMINI_MODEL

    def generate(self, prompt: str, model_name: str = None) -> str:
        target_model = model_name or self.default_model
        try:
            response = self.client.models.generate_content(
                model=target_model,
                contents=prompt
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Error in LLM generation ({target_model}): {e}")
            return f"Error generating response: {str(e)}"

    def generate_stream(self, prompt: str, model_name: str = None):
        target_model = model_name or self.default_model
        try:
            response_stream = self.client.models.generate_content_stream(
                model=target_model,
                contents=prompt
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Error in LLM streaming generation ({target_model}): {e}")
            yield f"\n[Error streaming response: {str(e)}]"

    def extract_metadata(self, content: str):
        prompt = f"""
You are an expert AI data organizer and Knowledge Graph constructor.
Analyze the following memory snippet and extract:
1. "category": A single-word string categorization of the memory (e.g. "architecture", "career", "personal", "database", "finance", etc. Use lowercase).
2. "tags": A list of relevant keywords or tags (lowercase strings).
3. "importance": A float between 0.0 and 1.0 representing how critical or foundational this memory is.
4. "relations": A list of extracted relationships for a Knowledge Graph. Each item should have "source" (string entity), "relation" (action e.g. "uses", "depends_on", "replaces"), and "target" (string entity).

Memory: "{content}"

Return ONLY a valid JSON object matching this schema:
{{
  "category": "string",
  "tags": ["string"],
  "importance": float,
  "relations": [
    {{"source": "string", "relation": "string", "target": "string"}}
  ]
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.default_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            category = str(data.get("category", "general")).lower().strip()
            tags = [str(t).lower().strip() for t in data.get("tags", [])]
            importance = float(data.get("importance", 0.5))
            relations = data.get("relations", [])
            return {
                "category": category,
                "tags": tags,
                "importance": max(0.0, min(1.0, importance)),
                "relations": relations
            }
        except Exception as e:
            logger.error(f"Error in metadata extraction: {e}")
            return {
                "category": "general",
                "tags": [],
                "importance": 0.5,
                "relations": []
            }

    def extract_multimodal_metadata(self, image_path: str, user_description: str = ""):
        try:
            image = Image.open(image_path)
            prompt = f"""
You are an expert AI system architect and visual analyst.
Analyze this uploaded image/diagram along with user note: "{user_description}".
Synthesize a clear, detailed memory description explaining what is shown (architecture diagram, UI design, bug traceback, or credentials).

Extract:
1. "content": A clear 2-3 sentence summary description of the diagram/image content and guidelines.
2. "category": A single-word category (lowercase).
3. "tags": A list of keyword tags (lowercase).
4. "importance": Float between 0.0 and 1.0.

Return ONLY a JSON object:
{{
  "content": "string",
  "category": "string",
  "tags": ["string"],
  "importance": float
}}
"""
            response = self.client.models.generate_content(
                model=self.default_model,
                contents=[image, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            return {
                "content": data.get("content", user_description or "Uploaded architectural asset"),
                "category": str(data.get("category", "architecture")).lower().strip(),
                "tags": [str(t).lower().strip() for t in data.get("tags", ["multimodal", "diagram"])],
                "importance": max(0.0, min(1.0, float(data.get("importance", 0.7))))
            }
        except Exception as e:
            logger.error(f"Error in multimodal extraction: {e}")
            return {
                "content": user_description or "Uploaded diagram/image note",
                "category": "architecture",
                "tags": ["multimodal"],
                "importance": 0.5
            }

    def compact_memories(self, memories_list: list) -> dict:
        formatted_memories = "\n".join([f"- ID {m['id']}: {m['content']}" for m in memories_list])
        prompt = f"""
You are an AI Memory Manager.
Synthesize and consolidate the following redundant memory snippets into a single, cohesive, authoritative memory snippet.
Combine duplicate information and remove outdated statements.

Memories:
{formatted_memories}

Return ONLY a JSON object:
{{
  "content": "A consolidated authoritative memory description.",
  "category": "single word category",
  "tags": ["tag1", "tag2"],
  "importance": float (0.0 to 1.0)
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.default_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error in memory compaction: {e}")
            return None