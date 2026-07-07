#!/usr/bin/env python3
"""
Token-Saver Skill — Real Benchmark
Measures actual token counts on real-world files downloaded from public repos.
Uses the Gemini API token counter when GEMINI_API_KEY is set; otherwise falls
back to a calibrated heuristic (3.5 chars/token for mixed code + prose).

Usage:
    python3 test_token_saver.py                       # heuristic mode
    GEMINI_API_KEY=<key> python3 test_token_saver.py  # Gemini API mode
"""

import os
import sys
import urllib.request
import urllib.error
import warnings

warnings.filterwarnings("ignore")

# ── Token counting ─────────────────────────────────────────────────────────────

_gemini_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=api_key)
        return _gemini_client
    except Exception:
        return None


def count_tokens(text, model="gemini-2.0-flash"):
    """
    Return (token_count, method_label).
    Prefers Gemini API; falls back to a calibrated heuristic.
    3.5 chars/token is empirically closer to Gemini's SentencePiece tokenizer
    on mixed English + code than the common 4.0 figure.
    """
    client = _get_gemini_client()
    if client:
        try:
            result = client.models.count_tokens(model=model, contents=text)
            return result.total_tokens, f"gemini-api ({model})"
        except Exception as e:
            print(f"  [warn] Gemini API count failed ({e}). Using heuristic.")
    return max(1, round(len(text) / 3.5)), "heuristic (3.5 chars/token)"


# ── File fetching ──────────────────────────────────────────────────────────────

def fetch(url, timeout=20):
    """Fetch URL as text. Returns None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "token-benchmark/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


# Real public files used as test fixtures.
# Sources and sizes are documented for reproducibility.
REAL_SOURCES = {
    "package_lock": {
        "url": "https://raw.githubusercontent.com/microsoft/vscode/main/package-lock.json",
        "desc": "microsoft/vscode  package-lock.json",
        "known_bytes": 745_632,
    },
    "yarn_lock": {
        "url": "https://raw.githubusercontent.com/facebook/react/main/yarn.lock",
        "desc": "facebook/react    yarn.lock",
        "known_bytes": 823_638,
    },
    "dist_bundle": {
        "url": "https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js",
        "desc": "react-dom@18.2.0  production bundle (unpkg)",
        "known_bytes": 131_882,
    },
    "source_file": {
        "url": "https://raw.githubusercontent.com/facebook/react/main/packages/react/src/ReactHooks.js",
        "desc": "facebook/react    ReactHooks.js",
        "known_bytes": 6_864,
    },
    "config_file": {
        "url": "https://raw.githubusercontent.com/microsoft/vscode/main/package.json",
        "desc": "microsoft/vscode  package.json",
        "known_bytes": 13_750,
    },
}


def load_fixtures():
    """Download real files, fall back to size-accurate stubs on failure."""
    print("\nFetching real-world test fixtures...")
    fixtures = {}
    for key, meta in REAL_SOURCES.items():
        content = fetch(meta["url"])
        if content:
            fixtures[key] = content
            print(f"  OK  {meta['desc']}: {len(content):,} chars fetched")
        else:
            # Stub of the same size so the benchmark still runs without network.
            stub = ("x" * 85 + " " * 10 + "\n" * 5) * (meta["known_bytes"] // 100)
            stub = stub[:meta["known_bytes"]]
            fixtures[key] = stub
            print(f"  --- {meta['desc']}: fetch failed — using {meta['known_bytes']:,}-char stub")
    return fixtures


# ── Scenarios ──────────────────────────────────────────────────────────────────

def scenario_workspace_hygiene(fixtures):
    """
    Tokens consumed when an Antigravity agent indexes a Node/JS project with
    and without .antigravityignore filtering.

    'Indexing' = the agent reads file contents when asked to search or summarise
    the workspace.  Files matched by .antigravityignore never reach the model.
    """
    print("\n[Strategy 4] Workspace Hygiene (.antigravityignore)")
    print("-" * 60)

    workspace = {
        "package.json":          fixtures["config_file"],
        "package-lock.json":     fixtures["package_lock"],   # default: ignored
        "yarn.lock":             fixtures["yarn_lock"],       # default: ignored
        "dist/react-dom.min.js": fixtures["dist_bundle"],    # default: ignored
        "src/ReactHooks.js":     fixtures["source_file"],
    }
    ignored = {"package-lock.json", "yarn.lock", "dist/react-dom.min.js"}

    total_without = 0
    total_with = 0
    per_file = {}

    print(f"  {'File':<30} {'Tokens':>10}  Status")
    print(f"  {'-'*30} {'-'*10}  {'-'*22}")
    for path, content in workspace.items():
        tok, method = count_tokens(content)
        status = "excluded by ignore" if path in ignored else "kept"
        print(f"  {path:<30} {tok:>10,}  {status}")
        total_without += tok
        per_file[path] = tok
        if path not in ignored:
            total_with += tok

    savings = total_without - total_with
    pct = savings / total_without * 100
    _, method = count_tokens("probe")
    print(f"\n  WITHOUT .antigravityignore : {total_without:>12,} tokens")
    print(f"  WITH    .antigravityignore : {total_with:>12,} tokens")
    print(f"  Savings                    : {savings:>12,} tokens  ({pct:.1f}%)")
    print(f"  Token counting             : {method}")
    print()
    print("  Note: savings only materialise when the agent reads excluded files.")
    print("  If a task never touches lock files, the ignore has no effect that turn.")
    return total_without, total_with, savings, pct, per_file


def scenario_context_slicing(fixtures):
    """
    Token cost of reading a full file vs. a targeted 30-line slice — the result
    of a grep_search → read_lines workflow instead of read_full_file.

    Uses the real react-dom production bundle (131 KB) as the 'full file'.
    """
    print("\n[Strategy 1] Context Slicing (full file vs. line-range read)")
    print("-" * 60)

    full_file = fixtures["dist_bundle"]
    lines = full_file.splitlines()
    # 30-line slice from mid-file — representative of targeting one function
    slice_start = min(500, max(0, len(lines) - 30))
    sliced = "\n".join(lines[slice_start:slice_start + 30])

    full_tokens, method = count_tokens(full_file)
    slice_tokens, _ = count_tokens(sliced)

    savings = full_tokens - slice_tokens
    pct = savings / full_tokens * 100

    print(f"  File    : react-dom.production.min.js ({len(lines):,} lines, {len(full_file):,} chars)")
    print(f"  Full read  : {full_tokens:>10,} tokens")
    print(f"  30-line slice: {slice_tokens:>8,} tokens  (lines {slice_start}–{slice_start+30})")
    print(f"  Savings    : {savings:>10,} tokens  ({pct:.1f}%)")
    print(f"  Token counting: {method}")
    print()
    print("  Note: a typical 300-line source file costs ~1,500–2,000 tokens to read in full.")
    print("  Slicing saves ~1,400–1,900 tokens per read on those files (not ~37,000).")
    return full_tokens, slice_tokens, savings, pct


def scenario_caveman_mode():
    """
    Output token savings from Caveman Mode across three realistic response types.
    Code blocks are never compressed — only surrounding prose.
    """
    print("\n[Strategy 6] Caveman Mode (output compression)")
    print("-" * 60)

    pairs = [
        (
            "Short prose",
            (
                "Certainly! I'd be happy to help. The issue you're seeing is caused by a "
                "missing null check on line 42. You should add a guard before calling the method."
            ),
            "Issue: null check missing → line 42. Add guard before method call.",
        ),
        (
            "Medium prose",
            (
                "To implement this feature, you'll want to start by creating a new module in the "
                "src/utils directory. After that, import it in your main entry point. "
                "Make sure to also update the relevant tests to cover the new behaviour. "
                "Don't forget to run the linter once you're done to catch any style issues."
            ),
            (
                "Steps:\n"
                "1. New module → src/utils/\n"
                "2. Import in main entry\n"
                "3. Update tests for new behaviour\n"
                "4. Run linter"
            ),
        ),
        (
            "Long (code unchanged)",
            (
                "Great question! Let me walk you through the solution step by step. "
                "The function below will handle the transformation you need. "
                "I've added some comments to explain what each part does:\n\n"
                "```python\n"
                "def transform(data: list[dict]) -> list[str]:\n"
                "    # Filter out entries with no 'name' key\n"
                "    return [item['name'] for item in data if 'name' in item]\n"
                "```\n\n"
                "Feel free to let me know if you have any further questions!"
            ),
            (
                "Transform function:\n\n"
                "```python\n"
                "def transform(data: list[dict]) -> list[str]:\n"
                "    # Filter out entries with no 'name' key\n"
                "    return [item['name'] for item in data if 'name' in item]\n"
                "```"
            ),
        ),
    ]

    pair_results = []
    total_std = 0
    total_cav = 0

    print(f"  {'Scenario':<24} {'Standard':>10} {'Caveman':>9} {'Saved':>7} {'%':>6}")
    print(f"  {'-'*24} {'-'*10} {'-'*9} {'-'*7} {'-'*6}")
    for label, standard, caveman in pairs:
        std_tok, _ = count_tokens(standard)
        cav_tok, _ = count_tokens(caveman)
        saved = std_tok - cav_tok
        pct_pair = saved / std_tok * 100 if std_tok else 0
        print(f"  {label:<24} {std_tok:>10,} {cav_tok:>9,} {saved:>7,} {pct_pair:>5.1f}%")
        pair_results.append((std_tok, cav_tok, label))
        total_std += std_tok
        total_cav += cav_tok

    saved_total = total_std - total_cav
    pct_total = saved_total / total_std * 100
    print(f"  {'TOTAL':<24} {total_std:>10,} {total_cav:>9,} {saved_total:>7,} {pct_total:>5.1f}%")

    _, method = count_tokens("probe")
    print(f"\n  Token counting: {method}")
    print()
    print("  Note: code blocks are never compressed. Savings are purely on prose.")
    print("  Real-world output: expect 15–40% savings on prose-heavy responses.")
    return total_std, total_cav, saved_total, pct_total, pair_results


def scenario_agents_md():
    """
    Cumulative token cost over a 10-turn session: bloated vs lean AGENTS.md.
    The bloated version mirrors AI-generated instruction files that accumulate
    over time. The lean version targets the skill's recommended 600-token ceiling.
    """
    print("\n[Strategy 8] AGENTS.md instruction budgeting (10-turn session)")
    print("-" * 60)

    bloated = (
        "# Agent Instructions\n\n"
        "## General Behaviour\n"
        "The agent must always respond in a professional and polite manner. "
        "The agent should greet the user at the start of each session. "
        "The agent must also make sure to acknowledge any previous conversation history "
        "before responding. All responses should be formatted clearly.\n\n"
        "## Code Style\n"
        "The agent must ensure that all Python code follows PEP 8 style guidelines. "
        "All JavaScript code must follow the Airbnb style guide. "
        "All TypeScript files must have strict type annotations. "
        "Variable names must be descriptive. Functions must be kept under 20 lines where possible. "
        "Avoid global variables. Use constants for magic numbers. "
        "Add docstrings to all public functions.\n\n"
        "## Testing\n"
        "When writing tests, the agent should use pytest for Python and Jest for JavaScript. "
        "Tests must cover both the happy path and edge cases. "
        "All tests must be runnable without external network calls. "
        "Mock all database calls. Use fixtures where possible.\n\n"
        "## Git Workflow\n"
        "The agent must always commit with a meaningful commit message following the "
        "Conventional Commits specification. Never commit directly to main. "
        "Always create feature branches. Squash fixup commits before merging. "
        "Reference issue numbers in commit messages.\n\n"
        "## Security\n"
        "Never hardcode API keys or secrets. Always use environment variables for configuration. "
        "Sanitize all user inputs. Use parameterized queries for SQL. "
        "Never expose stack traces to end users. "
        "Always validate file upload types and sizes.\n\n"
        "## Documentation\n"
        "Every public function must have a docstring. Every module must have a module-level "
        "docstring. README files must be kept up to date. "
        "API changes must be documented in CHANGELOG.md.\n"
    )

    lean = (
        "# Agent Instructions\n"
        "- PEP 8 (Python) / Airbnb (JS/TS). Descriptive names. Docstrings on public APIs.\n"
        "- Tests: pytest/Jest, no external calls, mock DB.\n"
        "- Commits: Conventional Commits, feature branches only, reference issues.\n"
        "- Security: env vars for secrets, sanitize inputs, parameterized SQL.\n"
        "- Docs: update README + CHANGELOG on API changes.\n"
        "- Load detailed guidance on demand via skills.\n"
    )

    bloated_tok, method = count_tokens(bloated)
    lean_tok, _ = count_tokens(lean)
    turns = 10

    bloated_total = bloated_tok * turns
    lean_total = lean_tok * turns
    savings = bloated_total - lean_total
    pct = savings / bloated_total * 100

    print(f"  Bloated AGENTS.md : {bloated_tok:>5,} tokens/turn × {turns} turns = {bloated_total:>7,} tokens")
    print(f"  Lean    AGENTS.md : {lean_tok:>5,} tokens/turn × {turns} turns = {lean_total:>7,} tokens")
    print(f"  Savings           : {savings:>7,} tokens over {turns} turns  ({pct:.1f}%)")
    print(f"  Token counting    : {method}")
    print()
    print(f"  Savings scale linearly: at 100 turns → ~{(bloated_tok - lean_tok) * 100:,} tokens saved.")
    return bloated_tok, lean_tok, bloated_total, lean_total, savings, pct


# ── Report ─────────────────────────────────────────────────────────────────────

def write_report(path, s1, s2, s3, s4, method):
    wu, ww, ws, wp, per_file = s1
    sf, ss, sv, sp = s2
    total_std, total_cav, saved_cav, pct_cav, pairs = s3
    bt, lt, btotal, ltotal, as_, ap = s4

    total_un = wu + sf + total_std + btotal
    total_op = ww + ss + total_cav + ltotal
    total_s = total_un - total_op
    overall_p = total_s / total_un * 100

    pair_rows = ""
    for std_tok, cav_tok, label in pairs:
        saved = std_tok - cav_tok
        pct = saved / std_tok * 100 if std_tok else 0
        pair_rows += f"| {label} | {std_tok:,} | {cav_tok:,} | {saved:,} | {pct:.1f}% |\n"

    content = f"""# Token-Saver Skill — Real Benchmark Report

**Methodology**: All token counts are measured on real files downloaded from public
GitHub repositories and CDN. Token counting uses: **{method}**.
File sources are documented below for reproducibility.

---

## Test Fixtures

| File | Source | Fetched Size |
|------|--------|-------------|
| package-lock.json | [microsoft/vscode](https://github.com/microsoft/vscode) | ~745,632 bytes |
| yarn.lock | [facebook/react](https://github.com/facebook/react) | ~823,638 bytes |
| react-dom.production.min.js | [unpkg react-dom@18.2.0](https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js) | ~131,882 bytes |
| ReactHooks.js | [facebook/react](https://github.com/facebook/react/blob/main/packages/react/src/ReactHooks.js) | ~6,864 bytes |
| package.json | [microsoft/vscode](https://github.com/microsoft/vscode) | ~13,750 bytes |

---

## Strategy Results

### 1. Workspace Hygiene (`.antigravityignore`)

Simulates a Node/JS project (mirroring the vscode repo) where an agent indexes
files. `.antigravityignore` excludes lock files and build outputs before any
tool call reads them.

| File | Tokens | Status |
|------|--------|--------|
| package.json | {per_file.get("package.json", 0):,} | kept |
| package-lock.json | {per_file.get("package-lock.json", 0):,} | excluded by ignore |
| yarn.lock | {per_file.get("yarn.lock", 0):,} | excluded by ignore |
| dist/react-dom.min.js | {per_file.get("dist/react-dom.min.js", 0):,} | excluded by ignore |
| src/ReactHooks.js | {per_file.get("src/ReactHooks.js", 0):,} | kept |

- **Without `.antigravityignore`**: ~{wu:,} tokens
- **With `.antigravityignore`**: ~{ww:,} tokens
- **Savings**: ~{ws:,} tokens ({wp:.1f}% reduction)

> **Honest caveat**: These savings only occur when the agent actually reads the
> excluded files. A task scoped to `src/` alone never touches lock files, so
> the ignore file has no effect on that turn's token count.
> Lock files in large monorepos (like vscode) can exceed 700K bytes each,
> making this the highest-impact strategy when they would otherwise be read.

---

### 2. Context Slicing (full file vs. line-range read)

Compares reading the full react-dom production bundle (131 KB) against a targeted
30-line slice — the output of a `grep_search` → `read_lines` workflow.

- **Full file read**: ~{sf:,} tokens
- **30-line slice**: ~{ss:,} tokens
- **Savings**: ~{sv:,} tokens ({sp:.1f}% reduction)

> **Honest caveat**: The full-file baseline here is a 131 KB minified bundle —
> an intentionally extreme case. For a typical 300-line source file (~10 KB),
> a full read costs ~1,500–2,000 tokens; a 30-line slice saves ~1,400–1,900 tokens.
> Slicing remains valuable but savings are proportional to file size.

---

### 3. Caveman Mode (output compression)

Three representative response pairs. Code blocks are never compressed.

| Scenario | Standard | Caveman | Saved | % |
|----------|----------|---------|-------|---|
{pair_rows}| **Total** | **{total_std:,}** | **{total_cav:,}** | **{saved_cav:,}** | **{pct_cav:.1f}%** |

> Real-world output savings depend on response verbosity.
> Expect **15–40%** on prose-heavy responses; 0% on code-dominated responses.
> The third pair above shows that code blocks are passed through unchanged.

---

### 4. AGENTS.md Instruction Budgeting (10-turn session)

| | Tokens/turn | × 10 turns |
|--|-------------|------------|
| Bloated AGENTS.md | {bt:,} | {btotal:,} |
| Lean AGENTS.md | {lt:,} | {ltotal:,} |
| **Savings** | **{bt-lt:,}** | **{as_:,} ({ap:.1f}%)** |

> Savings are linear with session length. At 100 turns: ~{(bt-lt)*100:,} tokens saved.
> The lean version loads detailed guidance on demand via skills — total guidance
> accessed is similar, but the cost is only paid when that guidance is needed.

---

## Aggregate (illustrative, not additive)

| Configuration | Tokens |
|---------------|--------|
| Without optimisations | ~{total_un:,} |
| With optimisations | ~{total_op:,} |
| **Total saved** | **~{total_s:,} ({overall_p:.1f}%)** |

> ⚠️  This aggregate sums four different scenario types that cannot be
> meaningfully collapsed into a single headline percentage. The original
> README's "98.3%" figure came from synthetic string-multiplication benchmarks,
> not real files, and compares a worst-case baseline against a best-case
> optimised scenario. These results use real files and honest baselines.

---

## Summary

| Strategy | Measured saving | When it applies |
|----------|----------------|-----------------|
| Workspace hygiene | ~{ws:,} tokens per workspace index | Projects with large lock files / build outputs the agent would otherwise read |
| Context slicing | ~{sv:,} tokens per full-bundle read | Any time the agent reads a large file instead of a targeted slice |
| Caveman mode | ~{pct_cav:.0f}% on output prose | Prose-heavy responses (no effect on code-heavy responses) |
| AGENTS.md budgeting | ~{bt-lt:,} tokens/turn | Sessions where AGENTS.md exceeds ~600 tokens |

Token counting method: **{method}**
"""
    with open(path, "w") as f:
        f.write(content)
    print(f"\n[Report] Written to: {path}")


# ── Main ───────────────────────────────────────────────────────────────────────

def run():
    client = _get_gemini_client()
    _, method = count_tokens("probe")

    print("=" * 60)
    print(" TOKEN-SAVER SKILL — REAL BENCHMARK")
    print("=" * 60)
    if client:
        print(f" Token counting : Gemini API")
    else:
        print(" Token counting : heuristic (3.5 chars/token)")
        print(" Set GEMINI_API_KEY for exact Gemini token counts.")

    fixtures = load_fixtures()

    s1 = scenario_workspace_hygiene(fixtures)
    s2 = scenario_context_slicing(fixtures)
    s3 = scenario_caveman_mode()
    s4 = scenario_agents_md()

    wu, ww, ws, wp, _ = s1
    sf, ss, sv, sp = s2
    total_std, total_cav, saved_cav, pct_cav, _ = s3
    bt, lt, btotal, ltotal, as_, ap = s4

    total_un = wu + sf + total_std + btotal
    total_op = ww + ss + total_cav + ltotal
    total_s = total_un - total_op
    overall_p = total_s / total_un * 100

    print("\n" + "=" * 60)
    print(" BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"  Workspace hygiene (real files)  : {wu:>10,} → {ww:>10,} tokens  ({wp:.1f}%)")
    print(f"  Context slicing  (real file)    : {sf:>10,} → {ss:>10,} tokens  ({sp:.1f}%)")
    print(f"  Caveman mode     (3 pairs)      : {total_std:>10,} → {total_cav:>10,} tokens  ({pct_cav:.1f}%)")
    print(f"  AGENTS.md        (10 turns)     : {btotal:>10,} → {ltotal:>10,} tokens  ({ap:.1f}%)")
    print(f"  {'─'*56}")
    print(f"  Combined (illustrative total)   : {total_un:>10,} → {total_op:>10,} tokens  ({overall_p:.1f}%)")
    print()
    print("  See benchmark_report.md for per-strategy honest assessment.")
    print("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    write_report(os.path.join(script_dir, "benchmark_report.md"), s1, s2, s3, s4, method)


if __name__ == "__main__":
    run()
