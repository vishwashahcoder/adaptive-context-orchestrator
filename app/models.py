from pydantic import BaseModel
from typing import List, Optional


class Memory(BaseModel):
    id: int
    content: str
    category: str
    importance: float
    timestamp: float
    tags: List[str]
    file_url: Optional[str] = None
    expires_at: Optional[float] = None

    model_config = {
        "from_attributes": True
    }


# REQUEST MODEL FOR ADDING MEMORY
class MemoryRequest(BaseModel):
    content: str
    category: str = "general"
    importance: float = 0.5
    tags: List[str] = []
    file_url: Optional[str] = None
    ttl_days: Optional[float] = None


# REQUEST MODEL FOR CHAT
class ChatRequest(BaseModel):
    query: str
    model_name: Optional[str] = "gemini-2.5-flash"


# REQUEST MODEL FOR MEMORY COMPACTION
class CompactionRequest(BaseModel):
    category: Optional[str] = None
    memory_ids: Optional[List[int]] = None