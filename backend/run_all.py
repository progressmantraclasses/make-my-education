"""
run_all.py — Runs all 7 required questions through answer.py and writes
verbatim output to answers.md.

Usage:
    python run_all.py
"""

import json
import subprocess
import sys

QUESTIONS = [
    "I scored 78% and have a budget of ₹1.5 lakh/year — which engineering colleges can I consider?",
    "Which colleges offer an MBA, and what do they cost?",
    "List the government colleges that have hostel facilities.",
    "What's the average placement package at North Ridge Institute of Technology?",
    "Does Ganga Valley University offer a PhD in Physics?",
    "Which colleges offer scholarships for students from low-income families?",
    "Which college is best for me? I have ₹1 lakh per semester.",
]


def run_question(question: str) -> str:
    """Run answer.py with a question and return the raw stdout."""
    result = subprocess.run(
        [sys.executable, "answer.py", question],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"ERROR running question: {question}", file=sys.stderr)
        print(f"stderr: {result.stderr}", file=sys.stderr)
        return json.dumps({
            "answer": f"ERROR: {result.stderr.strip()}",
            "citations": [],
            "answered": False,
            "reason_if_unanswered": "Script error",
        }, indent=2, ensure_ascii=False)
    return result.stdout.strip()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    lines: list[str] = ["# Answers\n"]
    lines.append("Verbatim, unedited output from `answer.py` for each of the 7 required questions.\n")
    lines.append("---\n")

    for i, question in enumerate(QUESTIONS, 1):
        print(f"[{i}/{len(QUESTIONS)}] {question}")
        output = run_question(question)
        lines.append(f"## Question {i}\n")
        lines.append(f"**Query:** `{question}`\n")
        lines.append("**Response:**\n")
        lines.append(f"```json\n{output}\n```\n")
        lines.append("---\n")
        print(f"  Done.\n")
        import time
        time.sleep(10)

    with open("answers.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"All {len(QUESTIONS)} questions answered. Output written to answers.md")


if __name__ == "__main__":
    main()
