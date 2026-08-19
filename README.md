# Make My Education — AI College Advisor

Make My Education is a full-stack AI advisory platform that helps students find and compare colleges. A student can ask a plain-English question like "Which engineering colleges can I afford under Rs 80,000 a year?" and the system retrieves, reasons over, and responds with a structured, grounded answer — complete with citations and follow-up suggestions.

The backend runs a strict Retrieval-Augmented Generation (RAG) pipeline. Every answer the LLM produces is anchored exclusively to the college dataset; the model cannot hallucinate data that isn't there.

---

## Technology Stack

### Frontend
- React 18 with Vite for fast development and optimised production builds.
- Custom CSS — glassmorphism UI, CSS variables for theming, flexible grid/flex layouts.
- react-markdown and remark-gfm to render LLM-generated Markdown tables, bold text, and lists correctly in the browser.

### Backend
- FastAPI (Python 3.11+) for async, high-performance REST endpoints.
- Pinecone Serverless as the vector database for semantic similarity search.
- sentence-transformers/all-MiniLM-L6-v2 runs locally — zero-cost embeddings, no external API call needed.
- Upstash Redis (Serverless) for query caching, keeping repeated queries near-instant and completely free.
- Groq-proxied LLMs: groq/compound-mini as the primary fast model and openai/gpt-oss-120b as the fallback for harder queries.

---

## Key Design Decisions

**Tiered LLM Fallback.** Every query is first attempted with the small, fast compound-mini model. If it fails or rate-limits, the system automatically retries with the 120B parameter model. This cuts average inference cost by over 80% while keeping reliability high.

**Universal JSON Mode.** The response format is set to `{"type": "json_object"}` rather than the strict json_schema mode. Enforcing the schema via prompt engineering is far more portable and token-efficient across model sizes.

**BLUF Formatting.** The system prompt enforces Bottom Line Up Front — the LLM must state its direct conclusion in the very first sentence, before tables or explanations. This makes answers immediately scannable.

**Regex Post-Processing.** After the LLM responds, the backend strips any internal college identifiers (e.g. C012) from both the answer text and follow-up questions before sending the response to the frontend. The user never sees raw system tokens.

**Local Embeddings.** Running all-MiniLM-L6-v2 locally drops embedding costs to zero permanently, while maintaining strong semantic match quality.

---

## Project Structure

```
make-my-education/
├── backend/
│   ├── api/                    # FastAPI app and route definitions
│   ├── services/
│   │   ├── cache_service.py    # Upstash Redis read/write logic
│   │   ├── retrieval_service.py # Pinecone semantic search + metadata filtering
│   │   ├── generation_service.py # LLM prompt, fallback logic, post-processing
│   │   ├── query_service.py    # Orchestrates the full RAG pipeline
│   │   ├── normalization_service.py # Fee unit detection (semester vs annual)
│   │   └── ingestion_service.py # CSV → structured chunks for Pinecone
│   ├── controllers/
│   │   └── query_controller.py
│   ├── config.py               # Central config (models, TOP_K, API keys)
│   ├── ingest.py               # One-time Pinecone ingestion script
│   ├── test_20.py              # 20-question automated evaluation suite
│   ├── answer.py               # CLI helper used by the test runner
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # AnswerCard, LoadingSpinner, etc.
│   │   ├── pages/              # HomePage
│   │   └── index.css           # Full design system
│   ├── vite.config.js
│   └── package.json
└── README.md
```

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/progressmantraclasses/make-my-education.git
cd make-my-education
```

### 2. Configure environment variables
Create a `.env` file inside the `backend/` folder:
```env
# backend/.env
GROQ_API_KEY="your_groq_or_proxy_api_key_here"
PINECONE_API_KEY="your_pinecone_api_key_here"
UPSTASH_REDIS_REST_URL="your_upstash_redis_url_here"
UPSTASH_REDIS_REST_TOKEN="your_upstash_redis_token_here"
```

### 3. Backend
```bash
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac / Linux)
source venv/bin/activate

pip install -r requirements.txt

# Ingest college data into Pinecone (run once, or after updating the CSV)
python ingest.py

# Start the API server
uvicorn api.app:app --reload
# Runs at http://localhost:8000
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

---

## Operations

**Run the 20-question evaluation suite**
```bash
cd backend
python test_20.py
```
Results are written progressively to `eval_results_20.md` so partial output is preserved even if the run is interrupted.

**Flush the Redis cache** (use this after modifying prompts or data)
```bash
cd backend
python -c "from services.cache_service import get_redis_client; get_redis_client().flushdb()"
```

---

## Evaluation Test Cases

The automated suite covers 20 real-world questions designed to stress-test every major edge case the system is expected to handle:

| # | Question | What it tests |
|---|----------|---------------|
| 1 | I scored 76%. Which engineering colleges can I apply to with a budget of Rs 1 lakh per year? | Combined cutoff + fee filter |
| 2 | Which government colleges in the dataset have the highest NAAC grade? | Categorical filter + ranking |
| 3 | Which is the oldest college in the dataset? | Numerical sort on metadata |
| 4 | What courses are available in Dehradun? | City-level filter |
| 5 | Compare the MBA colleges based on placement packages. | Multi-college comparison via Markdown table |
| 6 | Which colleges offer fee waivers for families earning less than Rs 5 lakh per year? | Nested text retrieval from narrative chunks |
| 7 | Which colleges have compulsory hostel accommodation? | Boolean metadata flag |
| 8 | Which colleges provide corporate mentorship to students? | Semantic search on "about" chunk |
| 9 | Does any college offer B.Tech in Biotechnology? | Empty-set query — correct "answered: true" with negative conclusion |
| 10 | What additional charges are mentioned for the hotel management college? | Fee detail retrieval from structured text |
| 11 | Which government colleges do not provide hostel facilities? | Negative filter — "government" AND "no hostel" |
| 12 | Is there any fee concession specifically for female students? | Narrative search for gender-specific schemes |
| 13 | A student scored 74%. Can they get admission to a college requiring 75% cutoff? | Edge-case eligibility reasoning (1 mark below cutoff) |
| 14 | Which colleges offer engineering degrees for less than Rs 60,000 per semester? | Unit conversion — semester vs annual fee normalisation |
| 15 | Does Shivalik Polytechnic offer a B.Tech degree? | Diploma vs Degree disambiguation guardrail |
| 16 | Why is the placement package recorded as 0 LPA for NIMS? | Zero-value interpretation (not reported, not worst) |
| 17 | Are Ganga Valley University and Ganga Institute of Commerce the same institution? | College name disambiguation |
| 18 | Which colleges are deemed universities and offer engineering courses? | Multi-condition: type = Deemed AND has engineering |
| 19 | What is the fee concession available at HCE for female students? | Specific institution + demographic retrieval |
| 20 | Engineering, no hostel required, budget Rs 80,000 per year | Multi-constraint query with optional hostel preference |

**Pass criteria:** A question passes if the LLM returns a valid JSON object with a non-empty `answer` field and `answered: true`. A question fails only when the API returns an error or the response cannot be parsed.

---

## Cost Estimation

Assumptions: ~2,500 input tokens and ~300 output tokens per query, 30% Redis cache hit rate, local embeddings (zero cost).

| Component | 1 Lakh queries (100k) | 1 Million queries (1M) |
|---|---|---|
| LLM Input Tokens | ~$8.75 | ~$87.50 |
| LLM Output Tokens | ~$1.68 | ~$16.80 |
| Pinecone Vector Search | ~$0.15 | ~$1.50 |
| Embeddings | $0.00 (local) | $0.00 (local) |
| Upstash Redis | ~$0.60 | ~$6.00 |
| **Total Estimated Cost** | **~$11.18 (approx Rs 930)** | **~$111.80 (approx Rs 9,300)** |

Cache hit rate directly impacts cost. At 50% cache hit rate (common for popular queries), the LLM cost above halves.
