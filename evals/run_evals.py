#!/usr/bin/env python3
"""
Token-Saver Skill — Eval Runner

Runs two eval suites and writes structured results to evals/results/eval_results.json.
Strictly requires the real Gemini API token counter. Mock/heuristic fallback is disabled.

  GEMINI_API_KEY=<key> python3 evals/run_evals.py

Exit code 0 = all evals passed. Non-zero = one or more failures.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "resources"))

from intercept_wasteful_prompts import analyze_prompt
import test_token_saver as bench

EVALSET_PATH    = os.path.join(SCRIPT_DIR, "interceptor_evalset.jsonl")
THRESHOLDS_PATH = os.path.join(SCRIPT_DIR, "benchmark_thresholds.json")
RESULTS_PATH    = os.path.join(SCRIPT_DIR, "results", "eval_results.json")

SEP = "─" * 60


# ── Interceptor suite ─────────────────────────────────────────────────────────

def run_interceptor_evals():
    print(f"\n{'='*60}")
    print(" SUITE 1: Prompt Interceptor")
    print(f"{'='*60}")

    cases = []
    with open(EVALSET_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    results = []
    passed = 0

    print(f"  {'ID':<16} {'Category':<14} {'Expected':<10} {'Actual':<10} {'Pass?'}")
    print(f"  {'-'*16} {'-'*14} {'-'*10} {'-'*10} {'-'*5}")

    by_category = {}
    for case in cases:
        _, actual_blocked = analyze_prompt(case["prompt"])
        expected = case["expected_blocked"]
        ok = actual_blocked == expected
        if ok:
            passed += 1

        by_category.setdefault(case["category"], {"pass": 0, "fail": 0})
        by_category[case["category"]]["pass" if ok else "fail"] += 1

        flag = "PASS" if ok else "FAIL"
        print(f"  {case['id']:<16} {case['category']:<14} {str(expected):<10} {str(actual_blocked):<10} {flag}")

        result_entry = {
            "id": case["id"],
            "category": case["category"],
            "prompt": case["prompt"],
            "expected_blocked": expected,
            "actual_blocked": actual_blocked,
            "pass": ok,
        }
        if "notes" in case:
            result_entry["notes"] = case["notes"]
        results.append(result_entry)

    failed = len(cases) - passed
    print(f"\n  Total: {len(cases)} | Passed: {passed} | Failed: {failed}")
    for cat, counts in sorted(by_category.items()):
        print(f"    {cat}: {counts['pass']} pass, {counts['fail']} fail")

    return {
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "by_category": by_category,
        "cases": results,
    }


# ── Benchmark suite ───────────────────────────────────────────────────────────

def run_benchmark_evals(thresholds):
    print(f"\n{'='*60}")
    print(" SUITE 2: Token-Saving Benchmarks")
    print(f"{'='*60}")

    import warnings
    warnings.filterwarnings("ignore")

    _, method = bench.count_tokens("probe")
    print(f"  Token counting: {method}\n")

    fixtures = bench.load_fixtures()

    wu, ww, ws, wp, per_file = bench.scenario_workspace_hygiene(fixtures)
    sf, ss, sv, sp           = bench.scenario_context_slicing(fixtures)
    ts, tc, sc, pc, pairs    = bench.scenario_caveman_mode()
    bt, lt, btotal, ltotal, sa, ap = bench.scenario_agents_md()

    scenarios = {
        "workspace_hygiene": {
            "savings_pct":    wp,
            "savings_tokens": ws,
            "without_tokens": wu,
            "with_tokens":    ww,
        },
        "context_slicing": {
            "savings_pct":    sp,
            "savings_tokens": sv,
            "without_tokens": sf,
            "with_tokens":    ss,
        },
        "caveman_mode": {
            "savings_pct":    pc,
            "savings_tokens": sc,
            "without_tokens": ts,
            "with_tokens":    tc,
        },
        "agents_md": {
            "savings_pct":    ap,
            "savings_tokens": sa,
            "without_tokens": btotal,
            "with_tokens":    ltotal,
        },
    }

    print(f"\n  {'Scenario':<22} {'Savings%':>9} {'Threshold':>10} {'Saved tok':>11} {'Min tok':>10} {'Pass?'}")
    print(f"  {'-'*22} {'-'*9} {'-'*10} {'-'*11} {'-'*10} {'-'*5}")

    passed = 0
    results = {}
    for name, data in scenarios.items():
        th = thresholds[name]
        pct_ok = data["savings_pct"] >= th["min_savings_pct"]
        tok_ok = data["savings_tokens"] >= th["min_savings_tokens"]
        ok = pct_ok and tok_ok
        if ok:
            passed += 1

        flag = "PASS" if ok else "FAIL"
        detail = ""
        if not pct_ok:
            detail += f" [pct {data['savings_pct']:.1f}% < {th['min_savings_pct']}%]"
        if not tok_ok:
            detail += f" [tok {data['savings_tokens']:,} < {th['min_savings_tokens']:,}]"

        print(
            f"  {name:<22} {data['savings_pct']:>8.1f}% {th['min_savings_pct']:>9.1f}%"
            f" {data['savings_tokens']:>11,} {th['min_savings_tokens']:>10,}  {flag}{detail}"
        )

        results[name] = {
            **data,
            "threshold_pct":    th["min_savings_pct"],
            "threshold_tokens": th["min_savings_tokens"],
            "pass": ok,
        }

    failed = len(scenarios) - passed
    print(f"\n  Total: {len(scenarios)} | Passed: {passed} | Failed: {failed}")

    return {
        "total": len(scenarios),
        "passed": passed,
        "failed": failed,
        "token_counting_method": method,
        "scenarios": results,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    with open(THRESHOLDS_PATH) as f:
        thresholds = json.load(f)
    # Strip the comment key if present
    thresholds = {k: v for k, v in thresholds.items() if not k.startswith("_")}

    interceptor_results = run_interceptor_evals()
    benchmark_results   = run_benchmark_evals(thresholds)

    total_pass = interceptor_results["passed"] + benchmark_results["passed"]
    total_fail = interceptor_results["failed"] + benchmark_results["failed"]
    total      = total_pass + total_fail
    pass_rate  = total_pass / total if total else 0.0

    print(f"\n{'='*60}")
    print(" OVERALL RESULT")
    print(f"{'='*60}")
    print(f"  Interceptor : {interceptor_results['passed']}/{interceptor_results['total']} passed")
    print(f"  Benchmarks  : {benchmark_results['passed']}/{benchmark_results['total']} passed")
    print(f"  Grand total : {total_pass}/{total} passed ({pass_rate*100:.0f}%)")
    if total_fail == 0:
        print("\n  ALL EVALS PASSED")
    else:
        print(f"\n  {total_fail} EVAL(S) FAILED")
    print(f"{'='*60}\n")

    output = {
        "run_date": "2026-07-07",
        "overall": {
            "total": total,
            "passed": total_pass,
            "failed": total_fail,
            "pass_rate": round(pass_rate, 4),
        },
        "interceptor": interceptor_results,
        "benchmarks": benchmark_results,
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results written to: {RESULTS_PATH}")

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
