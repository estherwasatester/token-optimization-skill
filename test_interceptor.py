#!/usr/bin/env python3
"""
Interactive Test for the Pre-Invocation Prompt Interceptor Hook
This script lets you test various prompt phrases against the classification rules
used by the token-saver hook.
"""

import sys
import os

# Import the analysis function from the resources folder
sys.path.append(os.path.join(os.path.dirname(__file__), "resources"))
try:
    from intercept_wasteful_prompts import analyze_prompt
except ImportError:
    # Inline fallback if import fails due to path differences
    def analyze_prompt(prompt):
        if not prompt:
            return None, False
        prompt_lower = prompt.lower().strip()
        vague_words = {"test", "go", "run", "do it", "do", "help", "hello", "hi", "ok", "okay", "yes", "no", "start", "proceed", "continue"}
        words = [w.strip("?,.!") for w in prompt_lower.split() if w.strip()]
        if len(words) <= 2 and any(w in vague_words for w in words):
            return "extremely vague and lacks details. Proceeding would trigger random directory lists or tool calls, consuming massive tokens.", True
        massive_keywords = ["print all", "show all", "dump all", "explain every", "everything", "all files", "entire codebase", "every file", "every line"]
        if any(keyword in prompt_lower for keyword in massive_keywords):
            return "requests a massive dump or explanation of the entire codebase. This will blow up the context window and exceed your token budget.", True
        loop_keywords = ["forever", "infinite", "loop", "over and over", "repeat"]
        if any(keyword in prompt_lower for keyword in loop_keywords) and ("print" in prompt_lower or "say" in prompt_lower or "run" in prompt_lower):
            return "requests an iterative or infinite repetition of a task, which risks triggering a high-turn agent loop.", True
        return None, False

def run_test():
    test_cases = [
        # ❌ Vague prompts
        "do it",
        "go",
        "run",
        "test?",
        # ❌ Massive dump requests
        "please print all files in the repository",
        "explain every line of code",
        "show me everything",
        # ❌ Loop requests
        "print hello forever",
        # ✅ Valid / safe prompts
        "implement a search function in database.py",
        "run the unit tests for auth module",
        "explain the token-saver skill architecture"
    ]

    print("=" * 70)
    print(" 🔍 PROMPT INTERCEPTOR HOOK TEST SUITE")
    print("=" * 70)
    print(f"{'PROMPT':<42} | {'STATUS':<8} | {'REASON / CLASSIFICATION'}")
    print("-" * 70)

    for prompt in test_cases:
        reason, is_stupid = analyze_prompt(prompt)
        status = "❌ BLOCKED" if is_stupid else "✅ PASSED"
        color = "\033[91m" if is_stupid else "\033[92m"
        reset = "\033[0m"
        
        display_prompt = f"\"{prompt}\""
        if len(display_prompt) > 40:
            display_prompt = display_prompt[:37] + "...\""
            
        print(f"{display_prompt:<42} | {color}{status:<8}{reset} | {reason or 'Valid developer query'}")

    print("=" * 70)
    print("\n💡 HOW TO TEST LIVE:")
    print("Simply type a vague prompt (like \"do it\" or \"go\") or a massive dump request")
    print("directly in your active Antigravity CLI chat. The registered hook will instantly")
    print("intercept the turn and guide the agent to halt and ask you for clarification.")
    print("=" * 70)

if __name__ == "__main__":
    run_test()
