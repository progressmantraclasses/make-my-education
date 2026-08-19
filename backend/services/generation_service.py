"""
generation_service.py
Responsibility: LLM answer generation only.
  - build_unit_instruction : select the right unit-conversion instruction string
  - build_system_prompt    : compose the full system prompt with context injected
  - parse_llm_response     : parse raw LLM text into response dict
  - generate_answer        : call Groq API and return structured answer dict
"""

import json
from typing import Any

from groq import Groq

import config


# ── Prompt constants ───────────────────────────────────────────────────────────

_SYSTEM_PROMPT_TEMPLATE = """You are a college advisor AI. Answer ONLY from the provided context about colleges. Never invent or guess information.

STRICT RULES:
1. **Citations**: Every factual claim must cite the college_id (e.g. C001). Always use the full college name AND college_id together on first mention to disambiguate — two colleges share the word "Ganga" in their names and are unrelated institutions in different cities.

2. **Fees**: The `annual_fees_inr` figure is per ACADEMIC YEAR, not per semester. It EXCLUDES hostel, mess, lab, studio, kit, and other charges which may be mentioned in the about text.
{unit_instruction}

3. **Budget questions**: When a user asks about budget or affordability, you MUST account for costs BEYOND tuition. If the about field mentions hostel charges, mess charges, lab fees, studio fees, kit charges, or any additional costs, mention them. A budget answer that only states tuition is incomplete and wrong.

4. **Cutoff**: `last_year_cutoff_pct` is a HARD FLOOR — the minimum aggregate percentage for eligibility last year. A student scoring below it was NOT eligible. Treat this as a strict filter, not a soft signal.

5. **Placements**: `avg_placement_lpa = 0` means placement data is NOT REPORTED or NOT APPLICABLE (e.g., medical/dental colleges where students do residencies instead). It does NOT mean worst placements. Never rank or name a college with 0 placement when asked about the "worst" or "lowest" placements.

6. **Diplomas vs Degrees**: A Diploma is NOT a degree. Diploma-only institutions (like polytechnics) should NOT be included when the user asks about "engineering colleges" or "degree colleges" unless the user explicitly asks about diplomas or polytechnics. Shivalik Government Polytechnic (C005) awards diplomas only, not B.Tech or any degree.

7. **Out of scope (CRITICAL)**: If the user asks for a field, course (e.g. Biotechnology), college, or topic NOT present in the provided context, you MUST set "answered": false, "citations": [], and provide the reason in "reason_if_unanswered". Do NOT set "answered": true and say "No, it is not offered". "answered": false is mandatory for anything missing from the data.

8. **Formatting**: You MUST wrap all College Names and Annual Fee amounts in **double asterisks** to bold them (e.g., **Indian Institute of Technology**, **₹2,00,000**). CRITICAL: Present your answer neatly using short paragraphs, bullet points, and line breaks for comparisons or lists. Never output a single dense block of text. Make the data easy to scan and read.

9. **Follow-ups**: Always generate 3 logical follow-up questions that the user might want to ask next. CRITICAL: The follow-up questions must be completely self-contained and explicit. Do NOT use pronouns like "these", "those", "it", or "this college". Explicitly name the colleges or entities you are referring to, so the question can be understood entirely on its own without prior conversation history (e.g., "What are the fee structures for Doon Business School and Ganga Valley University?" instead of "What are the fees for these colleges?").

10. **Response format**: You MUST respond with a valid JSON object with exactly these fields:
{{
  "answer": "Your detailed answer text here",
  "citations": ["C001", "C002"],
  "answered": true,
  "reason_if_unanswered": null,
  "follow_up_questions": ["Question 1?", "Question 2?", "Question 3?"]
}}
- If you cannot answer, set "answered" to false, "answer" to a brief explanation, "citations" to [], "reason_if_unanswered" to a clear reason, and provide related "follow_up_questions".
- The "citations" array must contain only college_id strings that you actually reference.

CONTEXT:
{context}
"""

_UNIT_INSTRUCTION_SEMESTER = """
- The user is asking about costs "per semester" or using semester language. Since fees in the data are per YEAR, you MUST convert: divide the annual fee by 2 and state the assumption explicitly, e.g. "≈ ₹X/semester, assuming two equal semesters per year". Also state the annual figure for clarity. Do NOT silently return the annual figure when the user asked per semester."""

_UNIT_INSTRUCTION_TOTAL = """
- The user is asking about total course cost or "in lakhs total". Since fees in the data are per YEAR, you MUST multiply by the course duration to estimate total cost, and state the assumption explicitly, e.g. "≈ ₹X total for a Y-year course". Also state the annual figure for clarity."""

_UNIT_INSTRUCTION_DEFAULT = ""


# ── Public functions ───────────────────────────────────────────────────────────


def build_unit_instruction(unit_type: str) -> str:
    """Return the appropriate unit-conversion instruction string for the prompt.

    Args:
        unit_type: 'semester' | 'total' | 'default'  (from normalization_service)
    """
    unit_map = {
        "semester": _UNIT_INSTRUCTION_SEMESTER,
        "total":    _UNIT_INSTRUCTION_TOTAL,
        "default":  _UNIT_INSTRUCTION_DEFAULT,
    }
    return unit_map.get(unit_type, _UNIT_INSTRUCTION_DEFAULT)


def build_system_prompt(context_str: str, unit_instruction: str) -> str:
    """Compose the full system prompt by injecting context and unit instruction."""
    return _SYSTEM_PROMPT_TEMPLATE.format(
        context=context_str,
        unit_instruction=unit_instruction,
    )


def parse_llm_response(raw_llm_text: str) -> dict[str, Any]:
    """Parse raw LLM text into the required response dict.

    On JSON parse failure: wraps the raw text in a safe fallback dict.
    Always ensures all 4 required fields exist.
    """
    try:
        parsed = json.loads(raw_llm_text)
    except json.JSONDecodeError:
        parsed = {
            "answer": raw_llm_text,
            "citations": [],
            "answered": False,
            "reason_if_unanswered": "Failed to parse LLM response as JSON.",
            "follow_up_questions": []
        }

    # Guarantee all required fields exist
    parsed.setdefault("answer", "")
    parsed.setdefault("citations", [])
    parsed.setdefault("answered", True)
    parsed.setdefault("reason_if_unanswered", None)
    parsed.setdefault("follow_up_questions", [])

    return parsed


def generate_answer(
    query: str,
    context_str: str,
    unit_type: str,
    groq_model_name: str,
) -> tuple[dict[str, Any], int, int]:
    """Call the Groq API and return a structured answer dict.

    Args:
        query           : original user question
        context_str     : merged college context from retrieval
        unit_type       : 'semester' | 'total' | 'default'
        groq_model_name : Groq model identifier string

    Returns:
        (response_dict, input_token_count, output_token_count)
    """
    unit_instruction = build_unit_instruction(unit_type)
    system_prompt = build_system_prompt(context_str, unit_instruction)

    groq_client = Groq(api_key=config.GROQ_API_KEY, max_retries=5, timeout=30.0)

    groq_response = groq_client.chat.completions.create(
        model=groq_model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": query},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1024,
    )

    raw_llm_text = groq_response.choices[0].message.content or "{}"
    input_token_count  = groq_response.usage.prompt_tokens     if groq_response.usage else 0
    output_token_count = groq_response.usage.completion_tokens if groq_response.usage else 0

    response_dict = parse_llm_response(raw_llm_text)

    return response_dict, input_token_count, output_token_count
