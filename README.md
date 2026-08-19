# Make My Education — RAG College Advisor Prototype

A Retrieval-Augmented Generation (RAG) CLI prototype that answers natural-language questions
about colleges, grounded strictly in a provided dataset of 15 synthetic colleges.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required environment variables:
```
GROQ_API_KEY=gsk_...
PINECONE_API_KEY=...
UPSTASH_REDIS_REST_URL=https://...upstash.io
UPSTASH_REDIS_REST_TOKEN=...
```

### 3. Ingest the data

```bash
python ingest.py
```

This reads `sample_colleges.csv`, creates 30 chunks (2 per college), embeds them with
`sentence-transformers/all-MiniLM-L6-v2`, and upserts into a Pinecone serverless index.
**Idempotent** — safe to re-run without creating duplicate vectors.

### 4. Ask a question

```bash
python answer.py "Which colleges offer an MBA, and what do they cost?"
```

### 5. Run all 7 required questions

```bash
python run_all.py
```

Generates `answers.md` with verbatim JSON outputs.

### 6. Run evaluation suite

```bash
python evals/run_evals.py
```

Runs 10 test cases and prints pass rate.

---

## Design Choices

### Chunking Strategy

Each of the 15 colleges produces **2 chunks** (30 total):

1. **Structured chunk** (`{college_id}_structured`): All columns flattened into a readable
   template string. `avg_placement_lpa = 0` is rendered as "Not reported / not applicable"
   to prevent the LLM from misinterpreting it.

2. **About-text chunk** (`{college_id}_about`): The raw `about` field, prefixed with the
   college name and ID for disambiguation. Kept separate because it's semantically different
   (unstructured narrative vs. tabular facts).

**Why 2 chunks, not 1?** The `about` field is ~110 words of narrative text that answers
different types of questions (scholarships, hostel charges, admission process) than the
structured fields. Keeping them separate improves retrieval precision — a scholarship
question will preferentially retrieve about-text chunks, while a fee comparison will
retrieve structured chunks.

### Caching Strategy

- **Upstash Redis** with REST API (serverless, HTTPS-only, no persistent connection needed)
- Cache key: SHA-256 hash of normalized query (lowercased, whitespace-collapsed)
- TTL: 24 hours (data may change)
- Cache hit → return immediately, no embedding/Pinecone/Groq calls
- Cache errors degrade gracefully (miss, not crash)

### Model Selection

- **Default**: `llama-3.1-8b-instant` ($0.05/1M input, $0.08/1M output) — cheapest/fastest
- **Escalation**: `llama-3.3-70b-versatile` triggered when:
  - Query contains comparison/ranking keywords AND retrieval returns >6 unique colleges
  - `USE_LARGE_MODEL=true` environment variable override
- Both models use `response_format={"type": "json_object"}` for structured output

### Metadata Filtering

Before vector search, regex extracts categorical filters from the query:
- "government"/"govt" → `type: Government`
- "private" → `type: Private`
- "hostel" → `hostel_available: Yes`
- City names → `city: {CityName}`

These become Pinecone metadata filters, narrowing scope before semantic search.

---

## Edge Case Handling

### 1. Per-Semester / Total-Cost Unit Language

**Approach chosen: Explicit conversion with stated assumption.**

Regex detects "per semester", "per sem", "in lakhs total", "total cost" in the query. When
detected, the system prompt instructs the LLM to:
- Convert the annual fee (divide by 2 for semester, multiply by course duration for total)
- State the assumption explicitly: "≈ ₹X/semester, assuming two equal semesters per year"
- Also state the annual figure for clarity

This avoids the worst failure (silently returning annual fee for a per-semester question)
while not over-asking for clarification on straightforward queries.

### 2. Cutoff as Hard Floor

`last_year_cutoff_pct` is encoded as a strict eligibility filter in:
- The structured chunk text: "Cutoff: {X}% (hard minimum aggregate)"
- The system prompt: "A student scoring below it was NOT eligible"

The LLM is instructed to treat it as a pass/fail gate, not a soft ranking signal.

### 3. Placement = 0 (C006 — Nainital Institute of Medical Sciences)

- Structured chunk renders as "Avg placement: Not reported / not applicable"
- System prompt: "0 means not reported. Check the about field for context."
- The about field explains: medical graduates go to internships and PG exams, not campus
  recruitment
- Never ranked as "worst placements"

### 4. Diploma ≠ Degree (C005 — Shivalik Government Polytechnic)

**Decision: EXCLUDE diploma-only institutions from "engineering college" queries.**

**Rationale:** C005 explicitly states "It does not award B.Tech or any degree." In common
educational parlance, "engineering college" implies a degree-granting institution offering
B.Tech/B.E. programs. A diploma polytechnic serves a different educational tier — students
typically use diplomas for lateral entry into degree programs elsewhere.

**Implementation:**
- System prompt instructs the LLM to exclude diploma-only institutions from "engineering
  college" or "degree college" queries
- C005 IS included when the user explicitly asks about "diploma", "polytechnic", or
  "technical education"
- This is a product judgment call, not a technical limitation

### 5. Similar Names (Ganga Valley University vs Ganga Institute of Commerce)

- `Ganga Valley University` (C002) — Haridwar, private university
- `Ganga Institute of Commerce` (C014) — Dehradun, private institute

**Disambiguation approach:**
- Every chunk's text includes both the full name AND college_id
- Metadata includes `college_id`, `name`, and `city`
- System prompt: "Two colleges share the word 'Ganga' — disambiguate by college_id AND full
  name"
- C014's about field explicitly notes: "unaffiliated with and unrelated to Ganga Valley
  University"

### 6. Budget Beyond Tuition

System prompt instructs: "When answering budget questions, account for costs BEYOND tuition."

Additional costs mentioned in about fields include:
- Hostel and mess charges (C001, C006, C009)
- Studio, material, printing charges (C008: ₹30k–40k/year)
- Uniform, knife-roll, kit charge (C010)
- Laboratory and dissertation charges (C013)
- Clinical material charges (C006)

### 7. Out-of-Scope Queries

System prompt instructs to set `answered: false` with a clear `reason_if_unanswered` when
the question asks about fields, courses, or colleges not in the dataset. Never guesses or
fabricates.

---

## Cost Table (Part D)

*Fill in after running `run_all.py` and `evals/run_evals.py` with actual measured data from `query_log.jsonl`.*

| Metric | Value |
|---|---|
| Avg input tokens/query | _TBD_ |
| Avg output tokens/query | _TBD_ |
| Avg end-to-end latency/query | _TBD_ |
| Model(s) used + cost/1M tokens | `llama-3.1-8b-instant` ($0.05 in / $0.08 out); `llama-3.3-70b-versatile` ($0.59 in / $0.79 out) as fallback |
| Cost per 1,000 queries (₹) | _TBD_ |
| One-time embedding cost for full dataset | $0.00 (local `all-MiniLM-L6-v2`, free) |
| Cache hit rate observed in testing | _TBD_ |

---

## Scaling Analysis (50,000 queries/month)

At 50,000 queries/month (~1,700/day), **latency breaks first**. Each cold query currently
loads the sentence-transformer model into memory on every invocation — at scale, the ~2–4s
model load time dominates. The fix is to run the embedding model as a persistent service
(FastAPI with the model loaded once at startup), which would cut per-query latency to
~50–100ms for embedding + network to Pinecone. Groq's API latency (~200–500ms) is already
fast.

Cost would be the second concern: at ~1,500 input tokens/query on the 8B model, 50K queries
would cost ~$3.75 input + ~$4 output ≈ $8/month (~₹670/month) — trivially cheap. But if
model escalation to 70B happens frequently, costs could rise ~10x.

Accuracy is least likely to break — the 15-row dataset is small and fully covered. The main
accuracy risk at scale is query diversity: novel phrasings that evade the metadata filters
or confuse retrieval.

---

## What I'd Do Differently With More Time

1. **Semantic caching (not just exact-match):** Currently, "MBA colleges?" and "colleges
   offering MBA programs" produce different cache keys. A semantic cache would embed the
   query and check for cosine similarity against cached query embeddings (e.g., similarity
   > 0.95 → cache hit). This would dramatically increase the cache hit rate for paraphrased
   queries.

2. **Smarter model routing/escalation:** Instead of simple regex + college-count heuristics,
   a lightweight classifier (or even a Groq call with the small model) could assess query
   complexity and route to 70B only for genuinely complex multi-hop reasoning. This would
   save cost while improving accuracy on hard queries.

3. **Hybrid search:** Combine vector search with keyword/BM25 search. For queries like
   "colleges with fee below 50,000", vector search alone is weak — a SQL-style filter on
   the `annual_fees_inr` column would be exact. A hybrid approach would let structured
   queries hit a filtered path while semantic queries use embeddings.

4. **Rule-based numeric guardrail layer:** Instead of letting the LLM regenerate fee and
   cutoff numbers freely from context, inject the exact retrieved values into a structured
   template that the LLM fills around. This would eliminate hallucinated numbers entirely —
   e.g., "The fee at {name} is ₹{fees}/year" is injected verbatim, and the LLM only
   generates the surrounding explanation. This is the single highest-ROI improvement for
   correctness.

---

## Project Structure

```
├── config.py              # Central config, env var loading, constants
├── ingest.py              # CSV → chunks → embeddings → Pinecone upsert
├── answer.py              # CLI query pipeline (cache → retrieve → generate)
├── run_all.py             # Runs 7 questions, generates answers.md
├── answers.md             # Verbatim output (generated)
├── query_log.jsonl        # Per-query metrics log (generated)
├── requirements.txt       # Python dependencies
├── .env.example           # Template env file
├── .gitignore             # Keeps secrets and build artifacts out
├── sample_colleges.csv    # Input data (15 colleges)
├── DATA_DICTIONARY.md     # Data dictionary with semantic rules
├── evals/
│   ├── test_cases.json    # 10 evaluation test cases
│   └── run_evals.py       # Eval runner with pass/fail reporting
└── README.md              # This file
```
