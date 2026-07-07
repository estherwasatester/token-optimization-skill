# 🪨 Token-Saver Skill for Antigravity

An [Antigravity](https://antigravity.google) skill that helps agents optimize Gemini token consumption and reduce costs on GCP / Agent Platform.

## What It Does

When activated, this skill guides agents to proactively reduce token usage through **9 complementary strategies**:

| # | Strategy | Impact |
|---|----------|--------|
| 1 | **Architectural & Tool Optimization** | Reduce static "token tax" from unused MCP servers and verbose tool outputs |
| 2 | **Multi-Model Routing** | Route routine tasks to Flash, reserve Pro for complex reasoning |
| 3 | **Vertex AI Context Caching** | Leverage GCP's lower-cost cached token pricing |
| 4 | **Workspace Hygiene** | Filter out `node_modules`, builds, and media via `.antigravityignore` |
| 5 | **Session Hygiene** | Prune history, fork conversations, reuse subagents |
| 6 | **"Caveman Mode"** | Compress agent output — strip filler, keep code exact |
| 7 | **Dynamic Tool & Prompt Filtering** | Load only relevant instructions, navigate by symbol not by file |
| 8 | **AGENTS.md Budget Rule** | Keep always-loaded config lean, refactor bloat into on-demand skills |
| 9 | **Pre-Invocation Hook** | Automatically scan, classify, and intercept vague or wasteful user prompts |

---

## 📈 Estimated Token Savings

According to our quantitative performance benchmarks, the combination of these strategies yields a massive **98.3% reduction in token consumption** during typical development turns:

| Workspace Scenario / Turn Type | Without Token-Saver | With Token-Saver | ✨ Savings |
|---------------------------------|---------------------|------------------|-----------|
| Workspace Indexing (no ignore)  | ~14,995 tokens      | ~222 tokens      | **98.5%** |
| Context Slicing (line-range)    | ~3,255 tokens       | ~12 tokens       | **99.6%** |
| Conversational Prose (Caveman)  | ~102 tokens         | ~37 tokens       | **63.7%** |
| Persisted Context (10-turn conversation) | ~20,300 tokens | ~400 tokens      | **98.0%** |
| **Total Cumulative Workflow Cost** | **~38,652 tokens**  | **~671 tokens**  | **98.3% (37.9k saved)** |

---

## 🛡️ Pre-Invocation Prompt Interceptor (Hook)

The repository includes a global `PreInvocation` hook script (`intercept_wasteful_prompts.py`) that acts as an active firewall for your wallet. It intercepts:
- **Extreme Vagueness**: Simple keywords like `"do it"`, `"run"`, `"go"`, or `"test"` with zero details.
- **Massive Data Dumps**: Vague requests like `"explain every line of code"` or `"show me everything"`.
- **Infinite Loops**: Endless looping routines.

When intercepted, the hook injects a transient warning prompting the agent to immediately halt and request clarification rather than executing expensive codebase scans.

### Registering the Hook Globally
To use the hook, copy it to your scratch directory and register it inside your global configuration file `~/.gemini/config/hooks.json`:

```json
{
  "gcs-brain-sync": {
    "PreInvocation": [
      {
        "type": "command",
        "command": "/Users/estherlloyd/.gemini/antigravity-cli/scratch/gcs_pre_invocation.py",
        "timeout": 10
      },
      {
        "type": "command",
        "command": "/Users/estherlloyd/.gemini/antigravity-cli/scratch/intercept_wasteful_prompts.py",
        "timeout": 10
      }
    ]
  }
}
```

---

## 🔬 Validation Techniques

We have provided two dedicated test scripts to quantitatively and interactively verify our token optimization techniques:

### 1. Quantitative Performance Simulator
Runs a mock JS/Node directory indexing, full-file vs sliced read, prose compression, and budget project to output exact token count tables.
```bash
python3 test_token_saver.py
```
*Creates/updates a local markdown verification report at [`benchmark_report.md`](benchmark_report.md).*

### 2. Interactive Prompt Interceptor Tester
Allows you to run static classification tests against various prompt examples to verify the interceptor hook logic.
```bash
python3 test_interceptor.py
```

---

## Installation

### Global (all workspaces)

Copy the skill into your Antigravity global config:
```bash
cp -r . ~/.gemini/config/skills/token-saver/
```

### Per-project

Copy the skill into your project's `.agents/skills/` directory:
```bash
mkdir -p .agents/skills/token-saver
cp -r . .agents/skills/token-saver/
```

### Via `skills.json` (shared teams)

Add a reference in your customization root's `skills.json`:
```json
{
  "entries": [
    { "path": "/path/to/token-optimization-skill" }
  ]
}
```

## Usage

The skill activates automatically when the agent detects keywords like:
- "reduce tokens", "save cost", "optimize context", "token budget"
- "workspace pruning", "context window bloating"

You can also explicitly ask: *"Use the token-saver skill"*.

### `.antigravityignore` Template

An example ignore file is included at [`resources/example-antigravityignore`](resources/example-antigravityignore). Copy it to your project root:
```bash
cp resources/example-antigravityignore /path/to/your/project/.antigravityignore
```

## Credits & Inspiration

- [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) — Caveman-style output compression
- [Elementor Engineers](https://medium.com/elementor-engineers/optimizing-token-usage-in-agent-based-assistants-ffd1822ece9c) — Lean tool management & dynamic filtering
- [Antigravity Docs](https://antigravity.google/docs) — Platform reference

## License

MIT
