import json
import os
import time
import numpy as np
from database import init_db, SessionLocal, MemoryModel, MemoryRelationModel

class MemoryEngine:

    def __init__(self):
        init_db()
        self._cache = None
        self.migrate_legacy_json()
        self.cleanup_expired_memories()

    def invalidate_cache(self):
        self._cache = None

    def cleanup_expired_memories(self):
        session = SessionLocal()
        try:
            now = time.time()
            expired = session.query(MemoryModel).filter(
                MemoryModel.expires_at.isnot(None),
                MemoryModel.expires_at < now
            ).all()
            if expired:
                print(f"Cleaning up {len(expired)} expired TTL memories...")
                for item in expired:
                    session.delete(item)
                session.commit()
                self.invalidate_cache()
        except Exception as e:
            print(f"Error cleaning expired memories: {e}")
        finally:
            session.close()

    def migrate_legacy_json(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        legacy_files = [
            os.path.join(base_dir, "data", "memories.json"),
            os.path.join(base_dir, "app", "data", "memories.json")
        ]
        
        session = SessionLocal()
        try:
            db_count = session.query(MemoryModel).count()
            if db_count > 0:
                return

            migrated_memories = []
            for file_path in legacy_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for item in data:
                                    if "content" in item:
                                        migrated_memories.append(item)
                    except Exception as e:
                        print(f"Error reading legacy file {file_path}: {e}")
            
            if migrated_memories:
                print(f"Migrating {len(migrated_memories)} legacy memories to SQLite database...")
                from retriever import Retriever
                retriever = Retriever()
                
                seen_content = set()
                for item in migrated_memories:
                    content_clean = item["content"].strip()
                    if content_clean in seen_content:
                        continue
                    seen_content.add(content_clean)
                    
                    exists = session.query(MemoryModel).filter(
                        MemoryModel.content == content_clean
                    ).first()
                    if exists:
                        continue
                        
                    embedding_vector = retriever.model.encode([item["content"]])[0]
                    
                    db_memory = MemoryModel(
                        content=content_clean,
                        category=item.get("category", "general"),
                        importance=item.get("importance", 0.5),
                        timestamp=item.get("timestamp", time.time()),
                        tags=json.dumps(item.get("tags", [])),
                        embedding=embedding_vector.astype(np.float32).tobytes()
                    )
                    session.add(db_memory)
                session.commit()
                print("Migration complete!")
                self.invalidate_cache()
        finally:
            session.close()

    def load_memories(self):
        # Return cached list if available to avoid DB deserialization bottleneck
        if self._cache is not None:
            return self._cache

        session = SessionLocal()
        try:
            db_memories = session.query(MemoryModel).all()
            memories = []
            for m in db_memories:
                embedding_arr = np.frombuffer(m.embedding, dtype=np.float32)
                memories.append({
                    "id": m.id,
                    "content": m.content,
                    "category": m.category,
                    "importance": m.importance,
                    "timestamp": m.timestamp,
                    "tags": json.loads(m.tags or "[]"),
                    "file_url": m.file_url,
                    "expires_at": m.expires_at,
                    "embedding": embedding_arr
                })
            self._cache = memories
            return memories
        finally:
            session.close()

    def save_memory(self, content, category, importance, tags, embedding_vector=None, file_url=None, ttl_days=None):
        session = SessionLocal()
        try:
            content_cleaned = content.strip()
            existing = session.query(MemoryModel).filter(
                MemoryModel.content == content_cleaned
            ).first()
            
            if existing:
                tags_list = json.loads(existing.tags or "[]")
                return {
                    "message": "Duplicate memory skipped",
                    "memory": {
                        "id": existing.id,
                        "content": existing.content,
                        "category": existing.category,
                        "importance": existing.importance,
                        "timestamp": existing.timestamp,
                        "tags": tags_list,
                        "file_url": existing.file_url,
                        "expires_at": existing.expires_at
                    }
                }
            
            if embedding_vector is None:
                from retriever import Retriever
                retriever = Retriever()
                embedding_vector = retriever.model.encode([content_cleaned])[0]
                
            expires_at = time.time() + (ttl_days * 86400) if ttl_days and ttl_days > 0 else None

            db_memory = MemoryModel(
                content=content_cleaned,
                category=category,
                importance=importance,
                timestamp=time.time(),
                tags=json.dumps(tags),
                embedding=embedding_vector.astype(np.float32).tobytes(),
                file_url=file_url,
                expires_at=expires_at
            )
            session.add(db_memory)
            session.commit()
            
            saved_id = db_memory.id
            self.invalidate_cache()

            return {
                "id": saved_id,
                "content": content_cleaned,
                "category": category,
                "importance": importance,
                "timestamp": db_memory.timestamp,
                "tags": tags,
                "file_url": file_url,
                "expires_at": expires_at
            }
        finally:
            session.close()

    def save_relations(self, source_content: str, relations: list):
        if not relations:
            return
        session = SessionLocal()
        try:
            source_mem = session.query(MemoryModel).filter(MemoryModel.content == source_content.strip()).first()
            if not source_mem:
                return
            for rel in relations:
                src_label = rel.get("source", "").strip()
                rel_type = rel.get("relation", "relates_to").strip()
                tgt_label = rel.get("target", "").strip()
                if src_label and tgt_label:
                    db_rel = MemoryRelationModel(
                        source_id=source_mem.id,
                        relation=rel_type,
                        target_id=source_mem.id
                    )
                    session.add(db_rel)
            session.commit()
        except Exception as e:
            print(f"Error saving relations: {e}")
        finally:
            session.close()

    def get_graph_data(self):
        session = SessionLocal()
        try:
            memories = session.query(MemoryModel).all()
            relations = session.query(MemoryRelationModel).all()
            nodes = [{"id": m.id, "label": m.content[:40] + "...", "category": m.category} for m in memories]
            edges = [{"from": r.source_id, "to": r.target_id, "label": r.relation} for r in relations]
            return {"nodes": nodes, "edges": edges}
        finally:
            session.close()

    def delete_memory(self, memory_id: int):
        session = SessionLocal()
        try:
            db_memory = session.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
            if not db_memory:
                return False
            session.delete(db_memory)
            session.commit()
            self.invalidate_cache()
            return True
        finally:
            session.close()

    def update_memory(self, memory_id: int, content: str = None, category: str = None, importance: float = None, tags: list = None):
        session = SessionLocal()
        try:
            db_memory = session.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
            if not db_memory:
                return None
            
            if content is not None:
                db_memory.content = content.strip()
                from retriever import Retriever
                retriever = Retriever()
                embedding_vector = retriever.model.encode([db_memory.content])[0]
                db_memory.embedding = embedding_vector.astype(np.float32).tobytes()
                
            if category is not None:
                db_memory.category = category
            if importance is not None:
                db_memory.importance = importance
            if tags is not None:
                db_memory.tags = json.dumps(tags)
                
            db_memory.timestamp = time.time()
            session.commit()
            self.invalidate_cache()
            
            return {
                "id": db_memory.id,
                "content": db_memory.content,
                "category": db_memory.category,
                "importance": db_memory.importance,
                "timestamp": db_memory.timestamp,
                "tags": json.loads(db_memory.tags or "[]")
            }
        finally:
            session.close()

    def export_to_markdown(self):
        memories = self.load_memories()
        lines = ["# Adaptive Context Orchestrator Memories\n"]
        lines.append(f"Exported at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        categories = {}
        for m in memories:
            cat = m.get("category", "general")
            categories.setdefault(cat, []).append(m)
            
        for cat, items in categories.items():
            lines.append(f"## Category: `{cat}`\n")
            for item in items:
                tags = ", ".join([f"#{t}" for t in item.get("tags", [])])
                lines.append(f"- **[Importance {item['importance']}]** {item['content']}  *(Tags: {tags})*")
            lines.append("\n")
            
        return "\n".join(lines)