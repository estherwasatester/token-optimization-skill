---
name: token-saver
description: |
  Clever strategies and guidelines to optimize token consumption and reduce costs in Antigravity when using Gemini on GCP/Agent Platform.
  Activate this skill when the user requests cost control, token optimization, workspace pruning, or when context windows are ballooning.
---

# Token-Saver: Cost & Token Optimization Guide

This skill provides actionable guidelines and templates for optimizing Gemini token usage in Antigravity, leveraging GCP Vertex AI context caching, model selection, and agent architecture best practices.

## 1. Architectural & Tool Optimization

*   **Lean Tool Registration**: Do not enable unused MCP servers. Every active MCP server registers its tool definitions in the system prompt, adding to the static "token tax" on every single turn.
*   **Minimal Tool Permissions**: When spawning subagents or running tasks, request only the narrowest possible permission scopes to avoid loading excessive resource metadata.
*   **Context Slicing**:
    - **Avoid reading full files**: Use the line-range arguments (`StartLine` and `EndLine`) in file-viewing tools to load only relevant functions or sections.
    - **Limit Command Outputs**: When running commands, filter or truncate verbose output (e.g., use `git diff --stat` or limit log length via `git log -n 5`) to prevent piping thousands of lines of terminal output back into the prompt context.

## 2. Multi-Model Routing

*   **Flash vs Pro**: 
    - Use `gemini-3.5-flash` or `gemini-3.5-flash-lite` for routine tasks (e.g., viewing files, formatting layouts, simple syntax fixes, listing directories, writing unit tests).
    - Reserve `gemini-3.5-pro` (or heavier reasoning models) for complex planning, system design, or multi-file debugging.
*   **Use `/btw` for Side-Queries**: In the Antigravity CLI, use the `/btw` command to ask quick questions. This prevents starting a full agent planning cycle, which executes multiple expensive reasoning turns.

## 3. Vertex AI Context Caching

*   **Static Context Ordering**: To trigger GCP Vertex AI context caching, place large static contexts (such as library documentations or large system prompts) at the *very beginning* of the context payload.
*   **Cache Lifetime**: Since context caching on GCP charges a lower rate for cached tokens, keep your session consistent and avoid changing initial system configurations or workspace paths mid-conversation, as doing so invalidates the cache.

## 4. Workspace Hygiene & File Filtering

*   **Implement `.antigravityignore`**: Prevent the agent from indexing and parsing binary, generated, or dependency files. Create an `.antigravityignore` file in your workspace root.
*   See the template in: [resources/example-antigravityignore](resources/example-antigravityignore)

## 5. Session Hygiene & History Management

*   **Prune Conversation History**: Conversation history grows cumulatively with each turn. Use the `/clear` or `/new` commands to clear the chat context once a sub-task is completed.
*   **Forking & Branching**: Use `/fork` or `/branch` to spin off a new conversation thread, carrying over only the current status instead of the full historical reasoning path.
*   **Reuse Subagents**: Instead of launching a new subagent for every task, send a new message to an existing idle subagent via `send_message` to save startup overhead.

## 6. "Caveman Mode" — Output Compression

Inspired by [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman). Compress what the agent *says*, not its reasoning quality.

**Rules when activated:**
*   Strip pleasantries, apologies, filler ("Certainly!", "I'd be happy to...", "Let me explain...").
*   Drop articles (*the*, *a*, *an*) and connective prose where clarity is preserved.
*   Use symbols: `→` for causality/flow, `=` for equivalence/assignment.
*   **Never compress**: code blocks, file paths, error messages, CLI commands, or safety warnings.
*   **Auto-clarity override**: If a high-risk operation is detected (file deletion, security rule changes, production deployments), automatically revert to full verbose explanations.

**Realistic expectations:** Output token savings of ~8–20% in agentic workflows. Most agent output is code and tool calls which cannot be compressed.

## 7. Dynamic Tool & Prompt Filtering

*   **Conditional Prompt Sections**: Only include instruction blocks relevant to the active tools. Don't load web development guidance for backend-only tasks.
*   **Symbol-Level Navigation**: Use `grep_search` to locate specific functions/classes *before* reading files. Avoid loading entire files to "find" something.
*   **Session-Level Caching**: If the same tool call (e.g., `list_dir` on a stable directory) has already been made in this session, reference the prior result instead of re-executing.
*   **Prune MCP Tool Schemas**: Each unused MCP tool adds ~200–500 tokens of schema to every turn. Disable MCP servers you are not actively using via `/mcp` or `mcp_config.json`.

## 8. AGENTS.md Budget Rule

*   Keep your `AGENTS.md` file under **600 tokens**. It is loaded into *every* conversation.
*   See the active workspace rules as a real-world example of a lean, optimized guideline prompt: [resources/AGENTS.md](resources/AGENTS.md)
*   If it exceeds 2,000 tokens, refactor task-specific instructions into dedicated `SKILL.md` files that load on-demand.
*   Periodically audit and prune `AGENTS.md` — AI-generated instructions tend to bloat over time.

## 9. Automated Pre-Invocation Prompt Interceptor (Hook)

*   **Prompt Interception**: A registered global `PreInvocation` hook (`intercept_wasteful_prompts.py`) scans user prompts on every turn.
*   **Vague/Wasteful Query Detection**: It checks for extremely vague prompts (e.g., short words like "go", "do it", "test" with no details) or massive print/dump requests (e.g., "explain every line in the codebase", "print everything") or infinite loops.
*   **Active Safeguard**: When a wasteful query is intercepted, the hook injects a system warning instructing the agent to **halt expensive tool execution** and prompt the user for clarification, preventing hundreds of dollars in wasted token expenses.

