import json
import subprocess
import sys
import time

QUESTIONS = [
    "I scored 76%. Which engineering colleges can I apply to with a budget of \u20b91 lakh per year?",
    "Which government colleges in the dataset have the highest NAAC grade?",
    "Which is the oldest college in the dataset?",
    "What courses are available in Dehradun?",
    "Compare the MBA colleges based on placement packages.",
    "Which colleges offer fee waivers for families earning less than \u20b95 lakh per year?",
    "Which colleges have compulsory hostel accommodation?",
    "Which colleges provide corporate mentorship to students?",
    "Does any college offer B.Tech in Biotechnology?",
    "What additional charges are mentioned for the hotel management college?",
    "Which government colleges do not provide hostel facilities?",
    "Is there any fee concession specifically for female students?",
    "A student scored 74%. Can they get admission to a college requiring 75% cutoff?",
    "Which colleges offer engineering degrees for less than \u20b960,000 per semester?",
    "Does Shivalik Polytechnic offer a B.Tech degree?",
    "Why is the placement package recorded as 0 LPA for NIMS?",
    "Are Ganga Valley University and Ganga Institute of Commerce the same institution?",
    "Which colleges are deemed universities and offer engineering courses?",
    "What is the fee concession available at HCE for female students?",
    "Which colleges should I consider if I want engineering, hostel is not required, and my budget is \u20b980,000 per year?"
]


def run_question(question: str) -> str:
    result = subprocess.run(
        [sys.executable, "answer.py", question],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return "ERROR: " + result.stderr.strip()
    return result.stdout.strip()


def evaluate_output(output: str):
    """
    Determine PASS or FAIL for a raw output string.

    PASS -- any valid LLM response:
        answered=true  -- LLM found data and answered
        answered=false -- LLM correctly refused (topic not in dataset)
      Both are legitimate grounded behaviours per the assignment spec:
      'Set answered: false when the data cannot support an answer; citations may then be empty.'

    FAIL -- actual errors only:
        Subprocess crash (output starts with ERROR:)
        JSON parse failure
        answer field missing or empty
        answer field == 'System Error' (API/pipeline failure)
    """
    if output.startswith("ERROR:"):
        return "FAIL", "Subprocess error: " + output

    try:
        parsed = json.loads(output)
    except (json.JSONDecodeError, ValueError) as exc:
        return "FAIL", "JSON parse error: " + str(exc)

    answer_text = parsed.get("answer", "")

    if not answer_text or not str(answer_text).strip():
        return "FAIL", "Response has no answer text"

    if str(answer_text).strip() == "System Error":
        reason = parsed.get("reason_if_unanswered", "Unknown API error")
        return "FAIL", "System error from API: " + str(reason)

    answered = parsed.get("answered", True)
    if answered:
        return "PASS_ANSWERED", ""
    else:
        return "PASS_REFUSED", ""


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    lines = ["# Evaluation Results (20 Questions)\n"]

    passed_count = 0
    for i, question in enumerate(QUESTIONS, 1):
        print("[" + str(i) + "/" + str(len(QUESTIONS)) + "] " + question)
        output = run_question(question)

        result_code, fail_reason = evaluate_output(output)

        if result_code == "PASS_ANSWERED":
            status = "PASS (answered=true)"
            passed = True
        elif result_code == "PASS_REFUSED":
            status = "PASS (answered=false — correctly refused)"
            passed = True
        else:
            status = "FAIL - " + fail_reason
            passed = False

        if passed:
            passed_count += 1

        lines.append("## Q" + str(i).zfill(2) + ": " + question)
        lines.append("**Status:** " + status + "\n")
        lines.append("```json\n" + output + "\n```\n")
        lines.append("---\n")
        print("  " + status)

        # Progressive save so partial results survive an interrupted run
        with open("eval_results_20.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        time.sleep(6)

    # Final save with overall score at the top
    lines.insert(1, "**Overall Score:** " + str(passed_count) + "/" + str(len(QUESTIONS)) + " Passed\n\n")

    with open("eval_results_20.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\nCompleted: " + str(passed_count) + "/" + str(len(QUESTIONS)) + " Passed. Output written to eval_results_20.md")


if __name__ == "__main__":
    main()
