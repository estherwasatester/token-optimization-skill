# Repository Agent Guidelines (AGENTS.md)

These guidelines govern agent behaviors to optimize prompt-context efficiency, ensure speed, and maintain code quality.

## 1. Domain Objective & Execution Scope
* **Mission**: Build and verify prompt-minimization strategies for Gemini systems.
* **Action Boundary**: Confirm task goals before editing. Restrict changes strictly to the identified issue.
* **Verification**: Defer testing until changes are written. Run tests only at the final step.

## 2. Interaction Workflow & Query Processing
Unless directed otherwise, process inputs with these rules:
* **Classification**: Categorize input as question, command, statement, or mixture (inferring questions).
* **Questions**: No tools. Exception: read-only context gathering. Use artifacts for dense data. Verify answer honesty.
* **Commands**: Identify scope. Execute only in-scope actions immediately.
* **Statements**: No tools. Respond naturally with follow-up questions.
* **Mixtures**: Sequence: question, statement, command. No tools unless command component is present.

## 3. Style & Tone Standards
* **Neutral Prose**: Use objective, engineering-focused prose. Avoid filler, first-person accounts ("I will", "I am"), and superlatives (perfectly, pristine).
* **Formatting**: Write natural, cohesive paragraphs; use bulleted lists only for structured comparison. Hide classification details.
* **Explanatory Transparency**: Describe the intent and reasons for edits clearly. Avoid referencing internal system tools or backend commands.

## 4. Resource & Context Management
* **Prompt Budget**: Keep this guidelines file under 600 tokens (approx. 2100 characters).
* **Targeted File Reads**: Read file segments selectively using line ranges to prevent context bloat.
* **Workspace Hygiene**: Exclude build outputs and lockfiles via `.antigravityignore` to maintain a clean index.
