import json
import subprocess
import sys
import time

QUESTIONS = [
    "I scored 76%. Which engineering colleges can I apply to with a budget of ₹1 lakh per year?",
    "Which government colleges in the dataset have the highest NAAC grade?",
    "Which is the oldest college in the dataset?",
    "What courses are available in Dehradun?",
    "Compare the MBA colleges based on placement packages.",
    "Which colleges offer fee waivers for families earning less than ₹5 lakh per year?",
    "Which colleges have compulsory hostel accommodation?",
    "Which colleges provide corporate mentorship to students?",
    "Does any college offer B.Tech in Biotechnology?",
    "What additional charges are mentioned for the hotel management college?",
    "Which government colleges do not provide hostel facilities?",
    "Is there any fee concession specifically for female students?",
    "A student scored 74%. Can they get admission to a college requiring 75% cutoff?",
    "Which colleges offer engineering degrees for less than ₹60,000 per semester?",
    "Does Shivalik Polytechnic offer a B.Tech degree?",
    "Why is the placement package recorded as 0 LPA for NIMS?",
    "Are Ganga Valley University and Ganga Institute of Commerce the same institution?",
    "Which colleges are deemed universities and offer engineering courses?",
    "What is the fee concession available at HCE for female students?",
    "Which colleges should I consider if I want engineering, hostel is not required, and my budget is ₹80,000 per year?"
]

def run_question(question: str) -> str:
    result = subprocess.run(
        [sys.executable, "answer.py", question],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"
    return result.stdout.strip()

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    lines = ["# Evaluation Results (20 Questions)\n"]
    
    passed_count = 0
    for i, question in enumerate(QUESTIONS, 1):
        print(f"[{i}/{len(QUESTIONS)}] {question}")
        output = run_question(question)
        
        # Evaluate Pass/Fail
        status = "❌ FAIL"
        try:
            parsed = json.loads(output)
            is_answered = parsed.get("answered", False)
            
            if is_answered:
                status = "✅ PASS"
        except Exception:
            pass # Failed to parse JSON or other error
            
        if "✅ PASS" in status:
            passed_count += 1
            
        lines.append(f"## Q{i:02d}: {question}")
        lines.append(f"**Status:** {status}\n")
        lines.append(f"```json\n{output}\n```\n")
        lines.append("---\n")
        print(f"  {status}")
        
        # Progressive save
        with open("eval_results_20.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        time.sleep(6)  # Avoid rate limits from custom proxy
        
    # Final save with overall score at the top
    lines.insert(1, f"**Overall Score:** {passed_count}/{len(QUESTIONS)} Passed\n\n")
    
    with open("eval_results_20.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"\nCompleted: {passed_count}/{len(QUESTIONS)} Passed. Output written to eval_results_20.md")

if __name__ == "__main__":
    main()
