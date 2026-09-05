import os
import sys
# Add current directory to path to resolve sibling imports when running from root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import shutil
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from sse_starlette.sse import EventSourceResponse
from typing import Optional

from memory_engine import MemoryEngine
from retriever import Retriever
from scorer import Scorer
from prompt_builder import PromptBuilder
from llm import GeminiLLM

from models import (
    Memory,
    MemoryRequest,
    ChatRequest,
    CompactionRequest
)
from config import AVAILABLE_MODELS

app = FastAPI(title="Adaptive Context Orchestrator", version="2.5.0")

memory_engine = MemoryEngine()
retriever = Retriever()
scorer = Scorer()
prompt_builder = PromptBuilder()
llm = GeminiLLM()

# Base directory for static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return {"message": "Adaptive Context Orchestrator API is running."}
    return FileResponse(index_path)

@app.get("/api/models")
def get_available_models():
    return {"models": AVAILABLE_MODELS, "default": AVAILABLE_MODELS[0]}

# REST API Endpoints
@app.get("/api/memories")
def get_memories(search: Optional[str] = None):
    memories = memory_engine.load_memories()
    memories_clean = []
    for m in memories:
        m_clean = {k: v for k, v in m.items() if k != "embedding"}
        memories_clean.append(m_clean)
        
    if search:
        search_lower = search.lower()
        memories_clean = [
            m for m in memories_clean
            if search_lower in m["content"].lower() or search_lower in m["category"].lower() or any(search_lower in t.lower() for t in m["tags"])
        ]
    return memories_clean

@app.post("/api/memories")
def create_memory(data: MemoryRequest):
    result = memory_engine.save_memory(
        content=data.content,
        category=data.category,
        importance=data.importance,
        tags=data.tags,
        file_url=data.file_url,
        ttl_days=data.ttl_days
    )
    if "message" in result and "Duplicate" in result["message"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=result["message"]
        )
    return result

@app.post("/api/memories/auto")
def create_memory_auto(data: dict):
    if "content" not in data or not data["content"].strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content field is required"
        )
    
    content = data["content"]
    ttl_days = data.get("ttl_days")
    extracted = llm.extract_metadata(content)
    
    result = memory_engine.save_memory(
        content=content,
        category=extracted["category"],
        importance=extracted["importance"],
        tags=extracted["tags"],
        ttl_days=ttl_days
    )
    
    # Save extracted graph relationships if available
    if extracted.get("relations"):
        memory_engine.save_relations(content, extracted["relations"])

    if "message" in result and "Duplicate" in result["message"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=result["message"]
        )
    return result

@app.post("/api/memories/upload")
async def upload_multimodal_memory(
    file: UploadFile = File(...),
    description: Optional[str] = Form("")
):
    filename = f"{int(os.path.getmtime(BASE_DIR))}_{file.filename}"
    file_path = os.path.join(UPLOADS_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    rel_url = f"/static/uploads/{filename}"
    extracted = llm.extract_multimodal_metadata(file_path, description)
    
    result = memory_engine.save_memory(
        content=extracted["content"],
        category=extracted["category"],
        importance=extracted["importance"],
        tags=extracted["tags"],
        file_url=rel_url
    )
    return result

@app.post("/api/memories/compact")
def compact_memories(data: CompactionRequest):
    memories = memory_engine.load_memories()
    if data.category:
        target_memories = [m for m in memories if m["category"].lower() == data.category.lower()]
    elif data.memory_ids:
        target_memories = [m for m in memories if m["id"] in data.memory_ids]
    else:
        target_memories = memories

    if len(target_memories) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need at least 2 memories to perform compaction."
        )

    compacted = llm.compact_memories(target_memories)
    if not compacted:
        raise HTTPException(status_code=500, detail="Compaction synthesis failed.")

    # Save consolidated memory and remove old memories
    new_mem = memory_engine.save_memory(
        content=compacted["content"],
        category=compacted.get("category", "general"),
        importance=compacted.get("importance", 0.8),
        tags=compacted.get("tags", ["compacted"])
    )
    for old in target_memories:
        memory_engine.delete_memory(old["id"])

    return {"message": "Memories compacted successfully", "new_memory": new_mem}

@app.get("/api/graph")
def get_graph():
    return memory_engine.get_graph_data()

@app.get("/api/memories/export")
def export_memories():
    md_content = memory_engine.export_to_markdown()
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=memories.md"}
    )

@app.put("/api/memories/{memory_id}")
def update_memory(memory_id: int, data: dict):
    result = memory_engine.update_memory(
        memory_id=memory_id,
        content=data.get("content"),
        category=data.get("category"),
        importance=data.get("importance"),
        tags=data.get("tags")
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory with ID {memory_id} not found"
        )
    return result

@app.delete("/api/memories/{memory_id}")
def delete_memory(memory_id: int):
    success = memory_engine.delete_memory(memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory with ID {memory_id} not found"
        )
    return {"message": "Memory deleted successfully", "id": memory_id}

@app.get("/api/stats")
def get_stats():
    memories = memory_engine.load_memories()
    if not memories:
        return {
            "total_memories": 0,
            "categories": {},
            "avg_importance": 0.0
        }
    
    categories = {}
    total_importance = 0.0
    for m in memories:
        cat = m.get("category", "general")
        categories[cat] = categories.get(cat, 0) + 1
        total_importance += m.get("importance", 0.5)
        
    return {
        "total_memories": len(memories),
        "categories": categories,
        "avg_importance": round(total_importance / len(memories), 2)
    }

@app.post("/api/chat")
def chat(data: ChatRequest):
    query = data.query
    model_name = data.model_name
    memories = memory_engine.load_memories()

    if not memories:
        return {
            "query": query,
            "retrieved_memories": [],
            "response": "No memories stored yet. Please add memories first."
        }

    retrieved = retriever.retrieve(query, memories)
    scored = scorer.score(retrieved)
    prompt = prompt_builder.build(query, scored)
    response = llm.generate(prompt, model_name=model_name)

    return {
        "query": query,
        "retrieved_memories": scored,
        "response": response
    }

@app.post("/api/chat/stream")
async def chat_stream(data: ChatRequest):
    query = data.query
    model_name = data.model_name
    memories = memory_engine.load_memories()

    if not memories:
        async def empty_gen():
            yield json.dumps({"type": "breakdown", "data": []}) + "\n"
            yield json.dumps({"type": "token", "data": "No memories stored yet. Please add memories first."}) + "\n"
        return EventSourceResponse(empty_gen())

    retrieved = retriever.retrieve(query, memories)
    scored = scorer.score(retrieved)
    prompt = prompt_builder.build(query, scored)

    async def event_generator():
        # First event: JSON context breakdown
        yield json.dumps({"type": "breakdown", "data": scored}) + "\n"
        # Subsequent events: token stream
        for token in llm.generate_stream(prompt, model_name=model_name):
            yield json.dumps({"type": "token", "data": token}) + "\n"

    return EventSourceResponse(event_generator())