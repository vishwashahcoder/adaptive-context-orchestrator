import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Float, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker

# Add app to path if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import SQLITE_DB_PATH

DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"

# Ensure parent directory of DB exists
os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class MemoryModel(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, default="general", index=True)
    importance = Column(Float, default=0.5)
    timestamp = Column(Float, nullable=False)
    tags = Column(String, default="[]")  # JSON string representation of tags list
    embedding = Column(LargeBinary, nullable=False)  # Stored numpy array of vector
    file_url = Column(String, nullable=True)  # URL/path to uploaded file/image
    expires_at = Column(Float, nullable=True)  # Optional TTL timestamp for auto-cleanup

class MemoryRelationModel(Base):
    __tablename__ = "memory_relations"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, index=True, nullable=False)
    relation = Column(String, nullable=False)  # e.g., "uses", "depends_on", "replaces"
    target_id = Column(Integer, index=True, nullable=False)

from sqlalchemy import create_engine, Column, Integer, String, Float, LargeBinary, text

def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE memories ADD COLUMN file_url VARCHAR"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE memories ADD COLUMN expires_at FLOAT"))
        except Exception:
            pass
        conn.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
