# 🧠 MemoryVault AI

> **A persistent, multimodal AI memory system powered by hybrid retrieval, reranking, and an agentic workflow.**

MemoryVault AI is a personal AI assistant that lets you **store, retrieve, and chat with your own memories**.

It combines multimodal ingestion, persistent storage, hybrid retrieval, CrossEncoder reranking, Gemini function calling, and LangGraph into one practical AI application.

---

## ✨ What is MemoryVault AI?

Traditional chat applications treat conversations as temporary.

MemoryVault takes a different approach:

```text
Memory Drop
     ↓
Extract / OCR / Transcribe
     ↓
Text
     ↓
Chunking
     ↓
Embeddings
     ↓
FAISS + BM25
     ↓
RRF Hybrid Retrieval
     ↓
CrossEncoder Reranking
     ↓
Gemini Agent
     ↓
Grounded Answer
```

The goal is simple:

> **Give an AI assistant a persistent memory that it can search and use when answering questions.**

---

# 🚀 Features

### 🧠 Persistent Memory

Store memories in a persistent SQLite-backed knowledge base and retrieve them across application restarts.

### 📥 Memory Drop

MemoryVault supports:

- 📄 PDF
- 📝 Text
- 🖼️ Image
- 🎧 Audio

Multiple files can be added in a single Memory Drop operation.

### 🔎 Hybrid Retrieval

MemoryVault combines:

- **FAISS** for semantic/vector retrieval
- **BM25** for lexical/keyword retrieval
- **RRF (Reciprocal Rank Fusion)** to combine retrieval results
- **CrossEncoder** reranking for final relevance ordering

### 🤖 Agentic Workflow

Gemini decides when a tool is required, while Python executes the tool.

Available tools:

| Tool | Purpose |
|---|---|
| `search_memory` | Search uploaded memories |
| `list_memories` | List available memories |
| `get_document_info` | Get information about a specific memory |
| `calculate` | Perform mathematical calculations |

The workflow is orchestrated using **LangGraph**.

### 💬 Persistent Conversations

Conversations and messages are stored in SQLite.

Supported operations include:

- Create new conversations
- Switch between conversations
- Persistent chat history
- Clear chat
- Delete conversations
- Automatic conversation naming

### 🏷️ Smart Naming

Direct text memories and conversations receive readable names using local Python logic.

This avoids an unnecessary additional Gemini API call.

### 🗂️ Search Scopes

Chat supports:

- **Current Memory**
- **Selected Memories**
- **All Memories**

### 📊 Dashboard

The dashboard provides:

- Memory statistics
- Memory details
- Categories
- Metadata
- Memory exploration
- Quick access to chat with a memory

### ⏰ Memory Recall

MemoryVault also includes a Memory Recall capability for scheduling future reminders around stored information.

---

# 🧩 Architecture

```text
                         ┌─────────────────────┐
                         │     Streamlit UI    │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        Memory Drop               Chat                Dashboard
              │                     │
              ▼                     ▼
      ┌───────────────┐      ┌───────────────┐
      │   Ingestion   │      │   LangGraph   │
      │    Pipeline   │      │     Agent     │
      └───────┬───────┘      └───────┬───────┘
              │                      │
              ▼                      ▼
          Chunking               Gemini
              │                      │
              ▼                      ▼
         Embeddings             Tool Calling
              │                      │
              ▼                      ▼
            FAISS              search_memory
              │                      │
              └──────────┬───────────┘
                         ▼
                 Hybrid Retrieval
                         │
                  ┌──────┴──────┐
                  ▼             ▼
                FAISS         BM25
                  │             │
                  └──────┬──────┘
                         ▼
                        RRF
                         │
                         ▼
                  CrossEncoder
                   Reranking
                         │
                         ▼
                  Relevant Context
                         │
                         ▼
                      Gemini
                         │
                         ▼
                   Final Answer
```

---

# 📥 Multimodal Ingestion

Different input types are converted into searchable text before entering the common RAG pipeline.

```text
PDF
 └── Text Extraction ─────┐
                         │
Image                    │
 └── OCR ────────────────┤
                         ├──→ Text → Chunking → Embeddings
Audio                    │
 └── Transcription ──────┤
                         │
Text ────────────────────┘
```

This keeps the retrieval architecture unified instead of creating separate retrieval systems for every modality.

---

# 🔎 Retrieval Pipeline

MemoryVault uses a multi-stage retrieval pipeline.

## 1. Dense Retrieval — FAISS

Embeddings are used to find semantically similar memory chunks.

This helps when the user's wording differs from the wording stored in memory.

## 2. Sparse Retrieval — BM25

BM25 provides keyword-based retrieval.

This is particularly useful for:

- Names
- Technologies
- Exact terms
- Project names
- Other lexical matches

## 3. Reciprocal Rank Fusion

FAISS and BM25 results are combined using RRF:

```text
FAISS results
      +
BM25 results
      ↓
     RRF
      ↓
Combined candidates
```

## 4. CrossEncoder Reranking

The candidate results are reranked using:

```text
cross-encoder/ms-marco-MiniLM-L-6-v2
```

The highest-quality context is then passed to the agent/answer-generation layer.

---

# 🤖 Agent Workflow

The agent uses Gemini function calling and LangGraph.

```text
User Question
      ↓
LangGraph Agent
      ↓
Does the question require a tool?
      │
   ┌──┴──┐
   │     │
  No    Yes
   │     │
   │     ▼
   │   Python Tool
   │     │
   │     ▼
   │   Tool Result
   │     │
   └──┬──┘
      ▼
   Gemini
      ↓
 Final Answer
```

Tool execution is performed in Python rather than asking the LLM to perform retrieval itself.

The agent also uses conversation history to resolve follow-up references such as:

> "What did I do there?"

---

# 🗂️ Search Scope

### Current Memory

Search only the currently selected memory.

### Selected Memories

Search a user-selected subset of memories.

### All Memories

Search across the complete memory collection.

---

# 💬 Conversation Memory

Conversation history is persisted in SQLite.

```text
User Question
      ↓
Save message
      ↓
Agent + memory retrieval
      ↓
Assistant Answer
      ↓
Save answer
```

This allows the application to maintain context across messages and application restarts.

---

# 🏷️ Smart Naming

MemoryVault avoids exposing timestamp-based internal names where possible.

For example:

```text
Before:
text_memory_20260905_005218_159307.txt

After:
My First Serious RAG Project.txt
```

Conversation example:

```text
Question:
Show all my Machine Learning projects.

Conversation:
Machine Learning Projects
```

Naming is performed locally, so it does **not create an additional Gemini API call**.

---

# 📊 Dashboard

The dashboard provides an overview of the user's stored memories.

It includes:

- Memory count
- Current session information
- Categories
- Metadata
- Memory details
- Memory exploration
- Chat access

---

# 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| UI | Streamlit |
| LLM | Google Gemini |
| Agent Workflow | LangGraph |
| Vector Retrieval | FAISS |
| Sparse Retrieval | BM25 |
| Hybrid Fusion | Reciprocal Rank Fusion (RRF) |
| Reranking | CrossEncoder |
| Database | SQLite |
| OCR | Image OCR pipeline |
| Audio | Audio transcription pipeline |

MemoryVault uses the **Google GenAI SDK directly** for Gemini integration and does not depend on LangChain.

---

# 📁 Project Structure

```text
MemoryVault-AI/
│
├── app.py
│
├── database/
│   └── db.py
│
├── frontend/
│   ├── sidebar.py
│   ├── upload_page.py
│   ├── chat_page.py
│   └── dashboard.py
│
├── rag/
│   ├── agent.py
│   ├── graph.py
│   ├── tools.py
│   ├── retriever.py
│   ├── memory_retriever.py
│   ├── hybrid_search.py
│   ├── bm25.py
│   ├── reranker.py
│   ├── query_rewriter.py
│   ├── query_router.py
│   ├── metadata_filter.py
│   ├── intent_router.py
│   ├── chain.py
│   ├── model.py
│   └── vectorstore.py
│
├── loaders/
│   ├── pdf_loader.py
│   ├── image_loader.py
│   └── audio_loader.py
│
├── data/
│   ├── uploads/
│   ├── vectorstore/
│   └── database/
│
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd MemoryVault-AI
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Gemini

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key
```

Never commit your `.env` file or API key to GitHub.

---

# ▶️ Running the Application

Start Streamlit:

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

---

# 🧪 Basic Usage

## 1. Store a memory

Open:

```text
Memory Drop
```

Add a PDF, text memory, image, or audio file.

Click:

```text
🧠 Store Memories
```

## 2. Open Chat

Navigate to:

```text
Chat
```

## 3. Select a scope

Choose:

```text
Current Memory
Selected Memories
All Memories
```

## 4. Ask questions

Examples:

```text
What technologies did I use to build MemoryVault?
```

```text
Show my Machine Learning projects.
```

```text
Where did I intern?
```

MemoryVault retrieves relevant memories and generates an answer from the available context.

---

# 🔐 Data & Privacy

MemoryVault stores application data under the project's `data/` directory:

```text
data/
├── database/
├── uploads/
└── vectorstore/
```

Gemini is used for AI operations that require model inference.

Do not upload sensitive information unless you understand how the configured AI services process submitted data.

---

# 💰 Cost-Conscious Design

A major design goal is to avoid unnecessary LLM/API calls.

Examples:

- FAISS retrieval runs locally.
- BM25 retrieval runs locally.
- RRF runs locally.
- CrossEncoder reranking runs locally.
- Memory naming uses local Python logic.
- Conversation naming uses local Python logic.
- Tool execution happens in Python.
- Agent tool calls are bounded.

This keeps Gemini focused on tasks where an LLM actually adds value.

---

# 🧪 Testing

The application has been tested across the following workflows:

- PDF ingestion
- Text memory ingestion
- Image OCR
- Audio transcription
- Multiple-file ingestion
- Duplicate-memory handling
- Current Memory retrieval
- Selected Memories retrieval
- All Memories retrieval
- Retrieval after application restart
- Persistent conversations
- Gemini function calling
- Memory listing
- Document information retrieval
- Mathematical calculations
- Smart naming

---

# 🎯 Project Status

## ✅ MemoryVault AI v1.0 — Complete

The core application is complete and functional.

The v1.0 architecture focuses on:

- Persistent memory
- Multimodal ingestion
- Hybrid retrieval
- Reranking
- Agentic tool calling
- Persistent conversations
- Practical user experience

Further experimentation can be developed as future versions rather than changing the stable v1.0 core.

---

# 🔮 Future Improvements

Possible v2 improvements include:

- Source-level citations
- Retrieval debugger
- Memory timeline
- Knowledge graph
- Memory editing
- Memory collections
- Advanced Memory Recall
- Authentication
- Cloud deployment
- Automated RAG evaluation
- Retrieval-quality metrics
- More advanced multimodal reasoning

---

# 👨‍💻 Author

**Abhishek**

MemoryVault AI was built as a hands-on journey through:

```text
Machine Learning
      ↓
NLP
      ↓
Deep Learning
      ↓
Transformers
      ↓
RAG
      ↓
Agents
      ↓
Complete AI Application
```

The project brings these concepts together into one working persistent-memory AI system.

---

# ⭐ Closing

MemoryVault AI is more than a chatbot.

It is an experiment in building an AI assistant that can **remember, retrieve, reason, and recall information over time**.

> **MemoryVault AI — Give your AI a memory.**
