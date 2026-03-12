<div align="center">

# 🧠 GNN Brain

### Interactive Graph Knowledge Chatbot

**Chat with any node in a 3D knowledge graph — students, teachers, projects, and more.**  
Powered by GNN-inspired retrieval, semantic search, and a rule-based AI engine.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-7+-646CFF?style=flat&logo=vite&logoColor=white)](https://vite.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🌟 What Is This?

**GNN Brain** is a full-stack AI chatbot that represents an institute's social and academic graph as an interactive 3D network. Click any node — a student, teacher, project, admin — and start a conversation. The AI answers intelligently using that node's graph context: connections, projects, concerns, interests, and more.

It simulates **Graph Neural Network reasoning** using FAISS semantic search + NetworkX graph expansion, without requiring heavy GNN training.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 **3D Interactive Graph** | Real-time force-directed graph with Three.js & react-force-graph-3d |
| 🤖 **AI Chatbot per Node** | Each node answers in-character based on its graph data |
| 🔍 **GNN-Style Retrieval** | FAISS vector search + NetworkX neighbor expansion |
| 💬 **Natural Language** | Ask in plain English — projects, concerns, connections, greetings |
| 🩷 **Project Nodes** | Students and teachers linked to real project nodes |
| ✨ **Source Highlighting** | Cited nodes glow gold in the 3D graph when the bot answers |
| 👋 **In-Character Greetings** | Say "hi" and each node introduces itself with its own data |

---

## 🗂️ Project Structure

```
GNN bot/
├── gnn-brain-backend/          # Python FastAPI backend
│   └── app/
│       ├── main.py             # FastAPI app + /graph, /path endpoints
│       ├── api/
│       │   └── chat.py         # POST /chat endpoint
│       ├── ai/
│       │   ├── llm.py          # Rule-based answer generator
│       │   ├── embedder.py     # Sentence transformer embeddings
│       │   └── prompt_templates.py
│       └── graph/
│           ├── data.py         # Node + edge definitions
│           ├── graph_builder.py
│           ├── retriever.py    # FAISS + NetworkX retrieval
│           └── brain.py        # ChatbotEngine orchestrator
│
└── gnn-brain-ui/               # React + Vite + TypeScript frontend
    └── src/
        ├── App.tsx             # 3D graph + side panel
        ├── ChatPanel.tsx       # Chat UI component
        └── App.css
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+

---

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/gnn-brain.git
cd "gnn-brain"
```

---

### 2. Backend Setup

```bash
cd gnn-brain-backend

# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --reload
```

✅ Backend running at **http://localhost:8000**

---

### 3. Frontend Setup

```bash
cd gnn-brain-ui
npm install
npm run dev
```

✅ Frontend running at **http://localhost:5173**

---

## 🔌 API Reference

### `GET /graph`
Returns all nodes and edges for the 3D graph visualization.

### `POST /chat`
Chat with a node using graph context.

**Request:**
```json
{
  "query": "What projects is this student working on?",
  "node": "Ananya Sharma"
}
```

**Response:**
```json
{
  "answer": "Ananya Sharma is currently working on the AI Chatbot project.",
  "sources": ["project_ai_chatbot", "S-A-3"]
}
```

---

## 💬 Example Conversations

| What you type | What the bot answers |
|---|---|
| `hi` | Node greets you in-character with its name, interest and project |
| `What projects is this student working on?` | Names the student's linked project |
| `What is this student worried about?` | Reads the student's concern from graph data |
| `Who is mentoring this project?` | Finds the connected Teacher node |
| `Tell me about yourself` | Full description from node metadata |
| `How are you connected to others?` | Shows graph path context |

---

## 🎨 Node Color Guide

| Color | Role |
|---|---|
| 🟢 Green | Section A Students |
| 🟠 Orange | Section B Students |
| 🟣 Indigo | Section C Students |
| 🟡 Yellow | HOD |
| 🔴 Red | Dean |
| 🔵 Sky Blue | Admin |
| 🩷 Pink | Projects |
| 🟪 Purple | Other |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, react-force-graph-3d, Three.js |
| **Backend** | FastAPI, Uvicorn, Python 3.10+ |
| **AI / Retrieval** | Sentence Transformers (`all-MiniLM-L6-v2`), FAISS, NetworkX |
| **Graph Engine** | Custom node/edge schema, GNN-style neighborhood expansion |

---

## 📄 License

[MIT](LICENSE) — free to use, fork, and build on.

---

<div align="center">
Made with ❤️ using FastAPI + React + NetworkX
</div>
