# Token-Saver Skill — Real Benchmark Report

**Methodology**: All token counts are measured on real files downloaded from public
GitHub repositories and CDN. Token counting uses: **heuristic (3.5 chars/token)**.
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
| package.json | 4,231 | kept |
| package-lock.json | 213,595 | excluded by ignore |
| yarn.lock | 235,325 | excluded by ignore |
| dist/react-dom.min.js | 37,681 | excluded by ignore |
| src/ReactHooks.js | 1,961 | kept |

- **Without `.antigravityignore`**: ~492,793 tokens
- **With `.antigravityignore`**: ~6,192 tokens
- **Savings**: ~486,601 tokens (98.7% reduction)

> **Honest caveat**: These savings only occur when the agent actually reads the
> excluded files. A task scoped to `src/` alone never touches lock files, so
> the ignore file has no effect on that turn's token count.
> Lock files in large monorepos (like vscode) can exceed 700K bytes each,
> making this the highest-impact strategy when they would otherwise be read.

---

### 2. Context Slicing (full file vs. line-range read)

Compares reading the full react-dom production bundle (131 KB) against a targeted
30-line slice — the output of a `grep_search` → `read_lines` workflow.

- **Full file read**: ~37,681 tokens
- **30-line slice**: ~4,213 tokens
- **Savings**: ~33,468 tokens (88.8% reduction)

> **Honest caveat**: The full-file baseline here is a 131 KB minified bundle —
> an intentionally extreme case. For a typical 300-line source file (~10 KB),
> a full read costs ~1,500–2,000 tokens; a 30-line slice saves ~1,400–1,900 tokens.
> Slicing remains valuable but savings are proportional to file size.

---

### 3. Caveman Mode (output compression)

Three representative response pairs. Code blocks are never compressed.

| Scenario | Standard | Caveman | Saved | % |
|----------|----------|---------|-------|---|
| Short prose | 43 | 19 | 24 | 55.8% |
| Medium prose | 84 | 30 | 54 | 64.3% |
| Long (code unchanged) | 117 | 53 | 64 | 54.7% |
| **Total** | **244** | **102** | **142** | **58.2%** |

> Real-world output savings depend on response verbosity.
> Expect **15–40%** on prose-heavy responses; 0% on code-dominated responses.
> The third pair above shows that code blocks are passed through unchanged.

---

### 4. AGENTS.md Instruction Budgeting (10-turn session)

| | Tokens/turn | × 10 turns |
|--|-------------|------------|
| Bloated AGENTS.md | 2,115 | 21,150 |
| Lean AGENTS.md | 528 | 5,280 |
| **Savings** | **1,587** | **15,870 (75.0%)** |

> Savings are linear with session length. At 100 turns: ~158,700 tokens saved.
> The lean version loads detailed guidance on demand via skills — total guidance
> accessed is similar, but the cost is only paid when that guidance is needed.

---

## Aggregate (illustrative, not additive)

| Configuration | Tokens |
|---------------|--------|
| Without optimisations | ~551,868 |
| With optimisations | ~15,787 |
| **Total saved** | **~536,081 (97.1%)** |

> ⚠️  This aggregate sums four different scenario types that cannot be
> meaningfully collapsed into a single headline percentage. The original
> README's "98.3%" figure came from synthetic string-multiplication benchmarks,
> not real files, and compares a worst-case baseline against a best-case
> optimised scenario. These results use real files and honest baselines.

---

## Summary

| Strategy | Measured saving | When it applies |
|----------|----------------|-----------------|
| Workspace hygiene | ~486,601 tokens per workspace index | Projects with large lock files / build outputs the agent would otherwise read |
| Context slicing | ~33,468 tokens per full-bundle read | Any time the agent reads a large file instead of a targeted slice |
| Caveman mode | ~58% on output prose | Prose-heavy responses (no effect on code-heavy responses) |
| AGENTS.md budgeting | ~1,587 tokens/turn | Sessions where AGENTS.md exceeds ~600 tokens |

Token counting method: **heuristic (3.5 chars/token)**
