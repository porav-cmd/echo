# 🚀 Enterprise Knowledge Assistant API

A production-grade, multi-tenant AI Knowledge Assistant built with **Django REST Framework**, **LangChain**, **LangGraph**, **Groq (Llama-3.3-70B)**, and **Google Gemini Embeddings**.

---

## 🌟 Key Features

- **🔒 Multi-Tenancy & Data Privacy**: Strict user isolation via JWT Authentication (`SimpleJWT`) and Vector Metadata Filtering (`user_id`). Users can only search and query their own uploaded documents.
- **🤖 LangGraph Agentic Workflow**: Stateful graph architecture featuring decoupled Nodes (`retrieve`, `generate`, `fallback`) and dynamic Conditional Router Edges to prevent AI hallucinations.
- **🎯 Multi-Agent Supervisor Router**: Intelligent intent classification node routing requests to specialized workers (`RAG Document Search`, `Code Developer Tool`, or `General Assistant`).
- **💾 Relational Database History**: Tracks uploaded document metadata and logs user chat histories in SQLite / PostgreSQL.
- **🚀 High-Speed LLM Inference**: Powered by Groq's `llama-3.3-70b-versatile` and Google's `text-embedding-004`.

---

## 🏗️ Architecture Overview

```
                               ┌────────────────────────────────┐
                               │     Client Request (cURL/Web)  │
                               └───────────────┬────────────────┘
                                               │ (Bearer JWT Token)
                               ┌───────────────▼────────────────┐
                               │   Django REST API Middleware   │
                               └───────────────┬────────────────┘
                                               │
                               ┌───────────────▼────────────────┐
                               │   Supervisor Intent Router     │
                               └───────────────┬────────────────┘
                                               │
         ┌─────────────────────────────────────┼─────────────────────────────────────┐
         │ Intent: RAG                         │ Intent: CODE                        │ Intent: GENERAL
         ▼                                     ▼                                     ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│       LangGraph Agent           │   ┌       Developer Code Agent      │   │      General Chat Agent         │
│ (Retrieve -> Grade -> Generate) │   │     (Groq Llama-3.3-70B)        │   │        (Greeting/Q&A)           │
└─────────────────────────────────┘   └─────────────────────────────────┘   └─────────────────────────────────┘
```

---

## 🛠️ API Reference Table

| Endpoint | Method | Auth Required | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/health/` | `GET` | ❌ No | Server health check endpoint |
| `/api/v1/register/` | `POST` | ❌ No | User signup & account creation |
| `/api/v1/token/` | `POST` | ❌ No | Obtain JWT Access & Refresh Tokens |
| `/api/v1/ingest/` | `POST` | 🔒 Yes | Parse, chunk, and embed documents for logged-in user |
| `/api/v1/ask/` | `POST` | 🔒 Yes | Basic RAG search & generation |
| `/api/v1/graph-ask/` | `POST` | 🔒 Yes | LangGraph stateful agent execution |
| `/api/v1/supervisor/` | `POST` | 🔒 Yes | Multi-Agent Supervisor intent router & execution |
| `/api/v1/history/` | `GET` | 🔒 Yes | Retrieve authenticated user's Q&A chat history |

---

## ⚡ Quickstart & Setup

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/your-username/knowledge-assistant.git
cd knowledge-assistant
python -m venv venv
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies
```bash
pip install django djangorestframework djangorestframework-simplejwt langchain langchain-community langchain-text-splitters langchain-google-genai langchain-groq langgraph python-dotenv pypdf requests
```

### 3. Configure Environment Variables (`.env`)
Create a `.env` file in the root folder:
```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

### 4. Run Migrations & Start Server
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Server will start at `http://127.0.0.1:8000/`.
