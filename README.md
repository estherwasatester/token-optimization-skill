# 🪨 Token-Saver Skill for Antigravity

An [Antigravity](https://antigravity.google) skill that helps agents optimize Gemini token consumption and reduce costs on GCP / Agent Platform.

## What It Does

When activated, this skill guides agents to proactively reduce token usage through 8 complementary strategies:

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
