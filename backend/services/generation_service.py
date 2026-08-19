"""
generation_service.py
Responsibility: LLM answer generation only.
  - build_unit_instruction : select the right unit-conversion instruction string
  - build_system_prompt    : compose the full system prompt with context injected
  - parse_llm_response     : parse raw LLM text into response dict
  - generate_answer        : call Groq API and return structured answer dict
"""

import json
import re
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

7. **Out of scope & Empty Sets (CRITICAL)**: If the data answers the question by confirming that 0 colleges match a criteria (e.g., "no colleges offer this" or "no colleges don't have a hostel"), you MUST set "answered": true, because you successfully answered the question! ONLY set "answered": false if the user's topic itself is completely unrelated/out-of-scope to the dataset and you cannot generate an answer at all. When "answered": false, provide the reason in "reason_if_unanswered".

8. **Direct Answer First (BLUF)**: Always give the direct, definitive answer in the very first sentence at the top. If 0 colleges match the criteria, state it immediately (e.g., "None of the colleges in the data match this criteria."). Provide your tables, lists, or detailed explanations ONLY AFTER the direct answer. Never put the conclusion at the bottom.

9. **Formatting & Structure (CRITICAL)**: You MUST format your answer using rich Markdown. Use **Markdown Tables** for comparisons between colleges. Use **Bold Headers** (###) to separate different parts of your answer. Use bullet points for lists. Wrap all College Names and Annual Fee amounts in **double asterisks** to bold them. Do NOT include the raw college IDs (like (C012), (C007)) in your visible text or follow-up questions; just use the college names. Never output a single dense block of text; your output must be a highly structured, scannable, and professional response.

10. **Follow-ups**: Always generate 3 logical follow-up questions that the user might want to ask next. CRITICAL: The follow-up questions must be completely self-contained and explicit. Do NOT use pronouns like "these", "those", "it", or "this college". Explicitly name the colleges or entities you are referring to. Do NOT include or mention the follow-up questions inside your main `"answer"` text string; they must ONLY be placed in the `"follow_up_questions"` JSON array.

11. **Response format**: You MUST respond with a valid JSON object with exactly these fields:
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


def parse_llm_response(raw_llm_text: str, force_error_reason: str = None) -> dict[str, Any]:
    """Parse raw LLM text into the required response dict.

    On JSON parse failure: wraps the raw text in a safe fallback dict.
    Always ensures all 4 required fields exist.
    """
    if force_error_reason:
        return {
            "answer": "System Error",
            "citations": [],
            "answered": False,
            "reason_if_unanswered": force_error_reason,
            "follow_up_questions": []
        }

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

    # Post-process: strip raw college IDs like (C012) from the text to ensure frontend cleanliness
    parsed["answer"] = re.sub(r"\s*\(C\d{3}\)", "", parsed["answer"])

    # Post-process: strip any "Follow-up Questions" / "Follow-ups" section the LLM appended
    # to the answer text — the frontend already renders follow_up_questions as buttons,
    # so any in-text copy creates a duplicate that confuses the user.
    parsed["answer"] = re.sub(
        r"\n+#{0,4}\s*follow[- ]?up[s]?.*",
        "",
        parsed["answer"],
        flags=re.IGNORECASE | re.DOTALL,
    ).rstrip()

    clean_followups = []
    for q in parsed["follow_up_questions"]:
        clean_followups.append(re.sub(r"\s*\(C\d{3}\)", "", str(q)))
    parsed["follow_up_questions"] = clean_followups

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

    max_attempts = 3
    for attempt in range(max_attempts):
        # Use the requested model for the first attempt, fallback to LARGE model on retries
        current_model = groq_model_name if attempt == 0 else config.GROQ_MODEL_LARGE
        
        try:
            groq_response = groq_client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": query},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048,
            )

            raw_llm_text = groq_response.choices[0].message.content or "{}"
            input_token_count  = groq_response.usage.prompt_tokens     if groq_response.usage else 0
            output_token_count = groq_response.usage.completion_tokens if groq_response.usage else 0

            response_dict = parse_llm_response(raw_llm_text)
            
            # If parsing succeeds without falling back to the error dict, return it
            if response_dict.get("reason_if_unanswered") != "Failed to parse LLM response as JSON.":
                return response_dict, input_token_count, output_token_count

        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"LLM Generation failed after {max_attempts} attempts: {e}")
                
                # Extract a friendly error message
                error_msg = str(e)
                if "rate_limit_exceeded" in error_msg.lower() or "429" in error_msg:
                    reason = "API Rate Limit Exceeded. Please try again in a few minutes."
                else:
                    reason = f"API Error: {error_msg}"
                
                return parse_llm_response("", force_error_reason=reason), 0, 0

    return parse_llm_response("", force_error_reason="Max retries reached."), 0, 0
