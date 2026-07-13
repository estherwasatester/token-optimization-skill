# Repository Agent Guidelines (AGENTS.md)

These instructions govern agent operations within this repository to preserve the context window, maximize execution speed, and uphold rigorous development standards.

## 1. Domain Objective & Execution Scope
* **Mission**: The primary objective of this repository is to construct, validate, and evaluate methods for optimizing prompt size and reducing operational costs within Gemini ecosystems.
* **Action Boundary**: Confirm specific goals and project boundaries prior to implementing any code adjustments. Restrict all edits and operations strictly to the identified issue to avoid unnecessary file changes.
* **Verification Policy**: To conserve API tokens and rate limits, defer all testing until after changes have been written. Run test suites only at the final step to validate the implementation.

## 2. Professional Tone & Descriptive Standards
* **Neutral Prose**: Employ factual, objective, and engineering-focused language in all communications. Eliminate non-essential conversational remarks, first-person accounts, and superlative praise or subjective judgments.
* **Explanatory Transparency**: Provide clear explanations of the design choices and reasons for modifications in responses. Do not discuss helper commands, file editing tools, or underlying infrastructure.

## 3. Resource Management & Context Conservation
* **System Prompt Budget**: Maintain a highly compact guidelines file (under 400 tokens) to prevent unnecessary context consumption during interaction rounds.
* **Targeted File Operations**: Access specific line ranges during file inspections to avoid pulling large, unnecessary text blocks into context.
* **Workspace Hygiene**: Keep the workspace clean and unburdened by leveraging `.antigravityignore` to filter out build artifacts, lockfiles, and temporary files.
