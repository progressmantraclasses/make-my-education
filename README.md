# Make My Education — RAG College Advisor 🎓

[![GitHub repository](https://img.shields.io/badge/GitHub-Repository-black?style=flat&logo=github)](https://github.com/progressmantraclasses/make-my-education)

A full-stack, enterprise-grade Retrieval-Augmented Generation (RAG) platform that provides accurate, strictly grounded answers to natural-language questions about colleges. 

The system leverages advanced semantic search, caching, and a modern React frontend to deliver a professional ChatGPT-like experience with auto-generated citations and follow-up questions.

---

## 🏗️ Architecture & Tech Stack

### Frontend (User Interface)
*   **Framework**: React 18 + Vite for blazing-fast HMR and building.
*   **Styling**: Vanilla CSS with a polished, modern, light-mode aesthetic (glassmorphism, interactive pill-buttons, smooth scroll).
*   **Features**: Auto-scrolling chat, citation chips, structured data rendering, and auto-generated follow-up questions.

### Backend (API & RAG Pipeline)
*   **Framework**: FastAPI (Python 3.11+) for high-performance async endpoints.
*   **Vector Database**: Pinecone (Serverless) for lightning-fast similarity search.
*   **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Local, zero-cost embedding).
*   **Caching Layer**: Upstash Redis (Serverless) for sub-100ms cache hits.
*   **LLM Provider**: Proxy-routed `openai/gpt-oss-120b` (Large) and `openai/gpt-oss-20b` (Small) for JSON-structured, highly grounded generation.

---

## 🚀 Quick Start Guide

### 1. Backend Setup
1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables (copy `.env.example` to `.env`):
   ```bash
   cp .env.example .env
   ```
   *Make sure your API keys (Pinecone, Upstash Redis, and LLM Proxy keys) are properly configured.*
4. **(Optional)** Run data ingestion to populate Pinecone:
   ```bash
   python ingest.py
   ```
5. Start the FastAPI server:
   ```bash
   uvicorn api.app:app --reload
   ```
   *The API will run at `http://localhost:8000`.*

### 2. Frontend Setup
1. Open a **new** terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:5173`.

---

## 🧪 Testing the RAG Pipeline

The backend includes automated testing scripts to evaluate the RAG pipeline against strict heuristics.

**1. Run the 20-Question Evaluation Suite:**
```bash
cd backend
python test_20.py
```
*This evaluates complex edge cases (e.g., negative filters, out-of-scope refusals, zero-value placement packages) and automatically grades them as ✅ PASS or ❌ FAIL. Results are saved in `eval_results_20.md`.*

**2. Run the Core 7 Questions (CLI Output):**
```bash
cd backend
python run_all.py
```

---

## 💸 Cost Optimization & Token Efficiency

This system is engineered for maximum accuracy while keeping token usage and latency strictly optimized.

### 1. Smart Caching (Sub-100ms Latency, Zero Cost)
*   **Upstash Redis**: Every incoming query is normalized (lowercased, whitespace collapsed) and SHA-256 hashed.
*   **Cache Hit**: Returns instantly without hitting Pinecone or the LLM. Completely bypasses input/output token costs.

### 2. Retrieval Tuning (TOP_K = 20)
*   We use a highly optimized chunking strategy (2 chunks per college: `structured` and `about`).
*   Instead of blindly fetching all data, `TOP_K` is carefully tuned to **20**. This ensures deep recall (finding hidden gems like fee waivers in long narratives) while preventing context-window bloat, saving massive amounts of input tokens.

### 3. Model Escalation
*   **Small Queries**: Default queries use a smaller proxy model (`openai/gpt-oss-20b`), saving ~80% on inference costs.
*   **Complex Queries**: If a query involves complex comparisons or requires deep reasoning across many retrieved chunks, the system can escalate to a heavier 120B parameter model.

### 4. Zero-Cost Local Embeddings
*   Instead of using OpenAI's paid `text-embedding-3-small`, the system uses the local `all-MiniLM-L6-v2` model. This drops embedding costs to **$0.00** forever, while maintaining exceptional semantic match quality.

---

## 🛡️ Edge Cases & Guardrails

1. **Out of Scope Protection**: If a user asks about a course not in the dataset (e.g., "Biotechnology"), the LLM is strictly prompted to return `answered: false` rather than hallucinating a polite "No".
2. **Follow-up Questions**: The LLM natively generates exactly 3 contextual follow-up questions alongside its answer. These are parsed in JSON and rendered as interactive chips in the UI.
3. **Data Disambiguation**: Colleges with similar names (e.g., "Ganga Valley University" vs "Ganga Institute of Commerce") are explicitly disambiguated in the prompts using unique `college_id` tags.

---

## 📂 Project Structure

```text
├── backend/
│   ├── api/                   # FastAPI routes (app.py, query_routes.py)
│   ├── services/              # Core logic (cache, retrieval, generation)
│   ├── config.py              # Central configuration (TOP_K, Models)
│   ├── test_20.py             # 20-Question Automated Evaluator
│   ├── ingest.py              # Pinecone Data Ingestion script
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # React components (AnswerCard, LoadingSpinner)
│   │   ├── pages/             # Main views (HomePage)
│   │   └── index.css          # Design system and aesthetic styling
│   ├── package.json           # Node dependencies
│   └── vite.config.js         # Frontend build configuration
└── README.md                  # This documentation
```
