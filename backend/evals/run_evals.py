"""
evals/run_evals.py — Runs all evaluation test cases, checks expectations,
and prints a pass rate with details on which cases failed.

Usage:
    python evals/run_evals.py
"""

import json
import os
import subprocess
import sys

EVALS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(EVALS_DIR)
TEST_CASES_FILE = os.path.join(EVALS_DIR, "test_cases.json")
QUERY_LOG_FILE = os.path.join(PROJECT_DIR, "query_log.jsonl")


def load_test_cases() -> list[dict]:
    """Load test cases from JSON file."""
    with open(TEST_CASES_FILE, encoding="utf-8") as f:
        return json.load(f)


def run_query(query: str) -> dict | None:
    """Run answer.py and return parsed JSON response."""
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_DIR, "answer.py"), query],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        return None
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        print(f"  ERROR: Could not parse output as JSON")
        return None


def check_cache_hit(query: str) -> bool:
    """Check if the last log entry for this query was a cache hit."""
    if not os.path.exists(QUERY_LOG_FILE):
        return False
    with open(QUERY_LOG_FILE, encoding="utf-8") as f:
        for line in reversed(f.readlines()):
            try:
                entry = json.loads(line.strip())
                if entry.get("query") == query:
                    return entry.get("cache_hit", False)
            except json.JSONDecodeError:
                continue
    return False


def evaluate_case(case: dict) -> tuple[bool, list[str]]:
    """Run a single test case and return (passed, list_of_failures)."""
    failures: list[str] = []
    query = case["query"]

    # For cache tests, run the query twice — first to prime, second to check cache
    if case.get("is_cache_test"):
        print(f"  Running first time (to prime cache)...")
        run_query(query)
        print(f"  Running second time (to check cache)...")
        response = run_query(query)
        if not check_cache_hit(query):
            failures.append("Expected cache hit on second run, but got cache miss")
    else:
        response = run_query(query)

    if response is None:
        failures.append("Failed to get a response from answer.py")
        return False, failures

    # Check 'answered' field
    if "expect_answered" in case:
        if response.get("answered") != case["expect_answered"]:
            failures.append(
                f"Expected answered={case['expect_answered']}, "
                f"got answered={response.get('answered')}"
            )

    # Check citations contain expected
    if case.get("expect_citations_contain"):
        actual_citations = set(response.get("citations", []))
        for cid in case["expect_citations_contain"]:
            if cid not in actual_citations:
                failures.append(f"Expected citation {cid} missing from {actual_citations}")

    # Check citations do NOT contain
    if case.get("expect_citations_not_contain"):
        actual_citations = set(response.get("citations", []))
        for cid in case["expect_citations_not_contain"]:
            if cid in actual_citations:
                failures.append(f"Citation {cid} should NOT be present but was found")

    # Check answer text contains expected phrases
    answer_text = response.get("answer", "").lower()
    if case.get("expect_answer_contains"):
        for phrase in case["expect_answer_contains"]:
            if phrase.lower() not in answer_text:
                failures.append(f"Expected phrase '{phrase}' not found in answer")

    # Check answer text does NOT contain certain phrases
    if case.get("expect_answer_not_contains"):
        for phrase in case["expect_answer_not_contains"]:
            if phrase.lower() in answer_text:
                failures.append(f"Phrase '{phrase}' should NOT be in answer but was found")

    passed = len(failures) == 0
    return passed, failures


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    test_cases = load_test_cases()
    print(f"Running {len(test_cases)} evaluation cases...\n")

    results: list[tuple[str, bool, list[str]]] = []

    for i, case in enumerate(test_cases, 1):
        case_id = case["id"]
        desc = case.get("description", "")
        print(f"[{i}/{len(test_cases)}] {case_id}: {desc}")
        print(f"  Query: \"{case['query']}\"")

        passed, failures = evaluate_case(case)
        results.append((case_id, passed, failures))
        import time
        time.sleep(10)

        if passed:
            print(f"  ✅ PASSED\n")
        else:
            print(f"  ❌ FAILED:")
            for f in failures:
                print(f"    - {f}")
            print()

    # Summary
    total = len(results)
    passed_count = sum(1 for _, p, _ in results if p)
    failed_count = total - passed_count

    print("=" * 60)
    print(f"RESULTS: {passed_count}/{total} passed ({100*passed_count/total:.0f}%)")
    print("=" * 60)

    if failed_count > 0:
        print(f"\nFailed cases:")
        for case_id, passed, failures in results:
            if not passed:
                print(f"  {case_id}:")
                for f in failures:
                    print(f"    - {f}")
    else:
        print("\n🎉 All cases passed!")


if __name__ == "__main__":
    main()
