# 🧠 Adaptive Context Orchestrator

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4.svg?logo=google&logoColor=white)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A high-performance, context-aware memory engine and semantic orchestrator for Large Language Models (LLMs). The orchestrator acts as a long-term semantic brain, enabling users and autonomous agents to persist notes, architectural decisions, and domain guidelines, dynamically retrieving and prioritizing relevant context using hybrid semantic + BM25 search with exponential time-decay re-ranking.

---

## ✨ Features & Capabilities

- ⚡ **100x Faster Retrieval**: Utilizes a local SQLite database storing pre-computed 384-dimensional vector embeddings serialized as binary BLOBs with fast NumPy dot-product similarity.
- 🔍 **Hybrid Retrieval Engine**: Combines 70% dense semantic search (`all-MiniLM-L6-v2`) with 30% sparse keyword matching (`BM25`).
- ⏳ **Time-Decay & Importance Scoring**: Blends relevance with configurable importance weights and exponential recency decay over a 72-hour half-life.
- 🤖 **AI Auto-Metadata Extraction**: Automatically parses unstructured notes using Gemini 2.5 Flash to extract categories, tags, and importance ratings on ingestion.
- 💬 **Context-Aware Streaming Chat**: Real-time Server-Sent Events (SSE) chat with live context inspection panels showing similarity metrics for each retrieved memory.
- 🎨 **Modern Dark-Mode Dashboard**: Built-in glassmorphic developer dashboard with interactive metrics, memory search, relation mapping, and knowledge management.

---

## 🛠️ System Architecture

### 1. Memory Ingestion Pipeline (`POST /api/memories/auto`)
```
[Unstructured Input Text] 
          │
          ▼
[Gemini 2.5 Flash] ──► Extracts category, tags, and importance rating.
          │
          ▼
[SentenceTransformer] ──► Encodes text into 384-dim dense vector.
          │
          ▼
[SQLite Storage] ────► Saves memory record with binary embedding BLOB.
```

### 2. Retrieval & Orchestration Pipeline (`POST /api/chat`)
```
[User Query]
     │
     ├─► [SentenceTransformer] ──► Encodes query into dense vector embedding.
     │
     ├─► [SQLite DB Read] ───────► Loads pre-computed candidate embeddings.
     │
     ▼
[Hybrid Retrieval Engine]
     ├─► Dense Semantic Similarity (70%) ──► Fast NumPy dot-product.
     ├─► Sparse BM25 Search (30%) ────────► Tokenized lexical matching.
     │
     ▼
[Time-Decay Re-ranking Scorer]
     └─► Final Score = (Retrieval * 0.5) + (Importance * 0.3) + (Recency Decay * 0.2)
     │
     ▼
[Prompt Orchestrator] ─────► Injects top-k memories as grounded context.
     │
     ▼
[Gemini 2.5 Flash] ────────► Streams contextualized response with citations.
```

---

## 📋 Prerequisites

- **Python 3.10+**
- A **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

---

## ⚙️ Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/vishwashahcoder/adaptive-context-orchestrator.git
cd adaptive-context-orchestrator
```

### 2. Configure Environment Variables
Copy the template and add your Gemini API key:
```bash
# On Linux/macOS
cp .env.example .env

# On Windows PowerShell
Copy-Item .env.example .env
```

Edit `.env` and set your key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Application
```bash
python -m uvicorn app.main:app --reload
```

Open your browser and visit: **[http://localhost:8000](http://localhost:8000)**

---

## 🖥️ Web Dashboard Overview

The dashboard is accessible directly at root (`/`):
- **📊 Overview**: Live metrics on stored memories, category distributions, and average importance scores.
- **📝 Memory Board**: Full CRUD interface for notes with AI auto-tagging, manual editing, and instant search.
- **💬 Assistant Chat**: Conversational interface with side-by-side **Retrieved Context Breakdown** showing exact score calculations for every retrieved memory snippet.

---

## 🔌 API Reference

### Memory Management
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/memories` | List all memories (supports `?search=` filter) |
| `POST` | `/api/memories` | Create a memory with manual metadata |
| `POST` | `/api/memories/auto` | Create a memory with Gemini auto-extracted metadata |
| `PUT` | `/api/memories/{id}` | Update existing memory content/metadata |
| `DELETE` | `/api/memories/{id}` | Delete a memory by ID |

### Chat & Analytics
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Query the orchestrator with contextual augmentation |
| `GET` | `/api/stats` | Retrieve aggregate database metrics |
| `GET` | `/api/models` | List available Gemini models |

---

## 📂 Project Structure

```
adaptive-context-orchestrator/
├── app/
│   ├── config.py             # System configuration & model hyperparameters
│   ├── database.py           # SQLite database schema and engine
│   ├── llm.py                # Gemini API integration & prompt execution
│   ├── main.py               # FastAPI application & REST/SSE endpoints
│   ├── memory_engine.py      # Core memory ingestion & lifecycle management
│   ├── models.py             # Pydantic schemas
│   ├── prompt_builder.py     # Context injection prompt engineering
│   ├── retriever.py          # Hybrid (Vector + BM25) retrieval engine
│   ├── scorer.py             # Time-decay re-ranking scoring algorithm
│   └── static/               # Frontend dashboard assets (HTML, CSS, JS)
│       └── uploads/          # Local storage for user attachments
├── data/
│   └── memories.json         # Default sample seed memories
├── .env.example              # Template environment file
├── .gitignore                # Git exclusion rules
├── LICENSE                   # MIT License
├── README.md                 # Project documentation
└── requirements.txt          # Python dependencies
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
