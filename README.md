<div align="center">

# ⚡ Codewise — AI Documentation Generator

**Automatically generate, search, and maintain structured documentation for any GitHub repository using LLMs.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Backend-000?logo=flask)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3-F55036)](https://groq.com)

</div>

---

## 📖 Overview

Codewise is a full-stack application that automates the generation of developer-friendly documentation from source code. Point it at any GitHub repository, and it will:

1. **Fetch** source files via the GitHub API.
2. **Generate** structured documentation (file summaries, function signatures, parameter details) using the **Groq LLM** (Llama 3.3 70B).
3. **Index** the documentation into a **FAISS** vector store for semantic search.
4. **Answer** natural-language questions about the codebase via a **RAG** (Retrieval-Augmented Generation) pipeline.
5. **Automate** the entire pipeline on every `git push` via a **GitHub Webhook** listener.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│   React 18 + Vite  (localhost:5173)                          │
│   ┌──────────┐  ┌──────────────┐  ┌────────────────┐        │
│   │ Sidebar  │  │   DocView    │  │  QueryPanel    │        │
│   │ (files)  │  │ (docs view)  │  │ (Q&A with AI)  │        │
│   └──────────┘  └──────────────┘  └────────────────┘        │
│   ┌──────────────────────────────────────────────────┐      │
│   │               StatusBar (trigger)                │      │
│   └──────────────────────────────────────────────────┘      │
└───────────────────────────┬──────────────────────────────────┘
                            │  fetch API
┌───────────────────────────▼──────────────────────────────────┐
│                     FLASK BACKEND (localhost:5000)            │
│                                                              │
│  Routes:                                                     │
│    GET  /health     → Health check                           │
│    GET  /docs       → Return all stored docs                 │
│    POST /trigger    → Run doc generation pipeline            │
│    POST /query      → RAG-powered Q&A                        │
│    POST /webhook    → GitHub push event listener             │
│                                                              │
│  Services:                                                   │
│    github_client  → Fetch file content from GitHub API       │
│    doc_generator  → LLM doc generation (Groq / static)       │
│    chunker        → Split docs into embeddable chunks        │
│    embedder       → Sentence-Transformers (MiniLM-L6-v2)     │
│    index_store    → FAISS vector index (build + search)       │
│    rag            → Retrieval-Augmented Generation Q&A        │
│                                                              │
│  Storage:                                                    │
│    data/docs.json   → Flat-file document store               │
│    data/chunks.json → Chunk metadata for vector search       │
│    data/faiss.index → FAISS binary index                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite 7 | Interactive UI with tab navigation, file browser, and Q&A panel |
| **Backend** | Flask, Flask-CORS | REST API server with blueprint-based routing |
| **LLM** | Groq (Llama 3.3 70B Versatile) | AI-powered documentation generation and Q&A answers |
| **Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) | 384-dimensional dense vectors for semantic search |
| **Vector Store** | FAISS (CPU) | Fast approximate nearest-neighbor search |
| **GitHub Integration** | GitHub REST API + Webhooks | File fetching and automated push-event triggers |
| **Storage** | JSON flat files | Lightweight document persistence (no database required) |

---

## 📁 Project Structure

```
Code_Nomad_Doc_Generator/
├── .env                          # Environment variables (API keys, secrets)
├── .gitignore
├── requirements.txt              # Python backend dependencies
├── verify_integration.py         # End-to-end integration test script
│
├── backend/
│   ├── app.py                    # Flask entry point & blueprint registration
│   ├── data/                     # Runtime data (auto-created, gitignored)
│   │   ├── docs.json             #   Generated documentation store
│   │   ├── chunks.json           #   Chunk metadata for search
│   │   └── faiss.index           #   FAISS vector index binary
│   ├── models/
│   │   └── doc_store.py          # Flat-file JSON persistence layer
│   ├── routes/
│   │   ├── docs.py               # GET /docs endpoint
│   │   ├── query.py              # POST /query endpoint (RAG Q&A)
│   │   ├── trigger.py            # POST /trigger endpoint (manual pipeline)
│   │   └── webhook.py            # POST /webhook endpoint (GitHub automation)
│   └── services/
│       ├── github_client.py      # GitHub API client (fetch file content)
│       ├── doc_generator.py      # LLM documentation generator (Groq + fallback)
│       ├── chunker.py            # Documentation chunking for embeddings
│       ├── embedder.py           # Sentence-Transformer encoder (+ fallback)
│       ├── index_store.py        # FAISS index builder & searcher
│       └── rag.py                # RAG pipeline (search + LLM answer)
│
└── frontend/
    ├── index.html                # HTML entry point
    ├── package.json              # Node.js dependencies
    ├── vite.config.js            # Vite dev server configuration
    └── src/
        ├── main.jsx              # React DOM entry point
        ├── App.jsx               # Root component (state, routing, API calls)
        ├── mockData.js           # Mock data for offline development
        ├── styles/
        │   └── index.css         # Global styles and design system
        └── components/
            ├── Sidebar.jsx       # File navigation sidebar
            ├── StatusBar.jsx     # Pipeline stats and trigger button
            ├── DocView.jsx       # Documentation viewer panel
            └── QueryPanel.jsx    # AI Q&A panel
```

---

## ⚙️ Environment Variables

Create a `.env` file in the **project root** with the following variables:

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | **Yes** | API key from [Groq Console](https://console.groq.com/). Powers doc generation and RAG Q&A. |
| `GITHUB_TOKEN` | **Yes** | GitHub Personal Access Token with `repo` scope. Used to fetch file contents. |
| `GITHUB_WEBHOOK_SECRET` | Optional | Shared secret for verifying GitHub webhook signatures (HMAC SHA-256). Required only if using webhooks. |

**Example `.env`:**
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
```

> **⚠️ Important:** Never commit your `.env` file. It is already in `.gitignore`.

---

## 🚀 How to Run (Step-by-Step)

### Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** and **npm** installed
- A **Groq API key** ([get one here](https://console.groq.com/))
- A **GitHub Personal Access Token** ([create one here](https://github.com/settings/tokens))

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/Abhishek690012/Code_Nomad_Doc_Generator.git
cd Code_Nomad_Doc_Generator
```

### Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# On Linux/macOS
cp .env.example .env

# Or manually create it and add:
GROQ_API_KEY=gsk_your_key_here
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your_secret_here
```

### Step 3: Set Up the Backend

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Start the Backend Server

```bash
cd backend
python app.py
```

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### Step 5: Set Up and Start the Frontend

Open a **new terminal** (keep the backend running):

```bash
cd frontend
npm install
npm run dev
```

You should see:
```
  VITE v7.3.3  ready in 277 ms

  ➜  Local:   http://localhost:5173/
```

### Step 6: Open the Application

Navigate to **http://localhost:5173** in your browser. You should see the Codewise UI.

### Step 7: Generate Documentation

1. Click **"Trigger Manual Run"** in the status bar. This sends a test request to the backend which fetches files from the configured repo and generates docs via the Groq LLM.
2. The **Sidebar** will populate with indexed files.
3. Click any file to view its AI-generated documentation.
4. Switch to the **"Ask the Codebase"** tab to ask natural-language questions about the code.

---

## 🔗 Setting Up the GitHub Webhook (Optional)

To automatically re-generate docs on every `git push`:

### 1. Expose your local server

Use [ngrok](https://ngrok.com/) to create a public URL for your local backend:

```bash
ngrok http 5000
```

Copy the `https://xxxx.ngrok-free.app` URL.

### 2. Add the webhook in GitHub

1. Go to your target repository → **Settings** → **Webhooks** → **Add webhook**.
2. **Payload URL:** `https://xxxx.ngrok-free.app/webhook`
3. **Content type:** `application/json`
4. **Secret:** The same value as `GITHUB_WEBHOOK_SECRET` in your `.env`.
5. **Events:** Select **"Just the push event"**.
6. Click **Add webhook**.

Now every push to that repository will automatically trigger documentation regeneration.

---

## 📡 API Reference

| Method | Endpoint | Description | Request Body |
|---|---|---|---|
| `GET` | `/health` | Health check | — |
| `GET` | `/docs` | Retrieve all generated documentation | — |
| `POST` | `/trigger` | Manually run the doc generation pipeline | `{"repo": "owner/repo", "files": ["path/to/file"]}` |
| `POST` | `/query` | Ask a question about the codebase (RAG) | `{"question": "How does auth work?"}` |
| `POST` | `/webhook` | GitHub webhook listener (push events) | *(sent automatically by GitHub)* |

---

## 🧪 Testing

Run the integration test script to verify all endpoints:

```bash
python verify_integration.py
```

Or test individual endpoints with `curl`:

```bash
# Health check
curl http://localhost:5000/health

# Trigger pipeline
curl -X POST http://localhost:5000/trigger \
  -H "Content-Type: application/json" \
  -d '{"repo": "octocat/Hello-World", "files": ["README"]}'

# Get all docs
curl http://localhost:5000/docs

# Ask a question
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What does this codebase do?"}'
```

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Commit your changes: `git commit -m "Add my feature"`.
4. Push to the branch: `git push origin feature/my-feature`.
5. Open a Pull Request.

---

## 📄 License

This project is open-source. See the repository for license details.

---

<div align="center">
  <sub>Built with ⚡ by the Code Nomad team</sub>
</div>