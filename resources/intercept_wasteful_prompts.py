#!/usr/bin/env python3
import sys
import json
import os

def load_last_user_prompt(transcript_path):
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    try:
        user_prompt = None
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("source") == "USER_EXPLICIT" and data.get("type") == "USER_INPUT":
                        content = data.get("content", "")
                        # Parse user request block if present
                        if "<USER_REQUEST>" in content:
                            start = content.find("<USER_REQUEST>") + len("<USER_REQUEST>")
                            end = content.find("</USER_REQUEST>")
                            req = content[start:end].strip() if end != -1 else content[start:].strip()
                        else:
                            req = content.strip()
                        user_prompt = req
                except Exception:
                    pass
        return user_prompt
    except Exception:
        return None

def analyze_prompt(prompt):
    if not prompt:
        return None, False
    
    prompt_lower = prompt.lower().strip()
    
    # Define trigger categories
    
    # 1. Extreme Vagueness (short and meaningless)
    vague_words = {"test", "go", "run", "do it", "do", "help", "hello", "hi", "ok", "okay", "yes", "no", "start", "proceed", "continue"}
    words = [w.strip("?,.!") for w in prompt_lower.split() if w.strip()]
    
    if len(words) <= 2 and any(w in vague_words for w in words):
        return "extremely vague and lacks details. Proceeding would trigger random directory lists or tool calls, consuming massive tokens.", True
        
    # 2. Massive Data Dump Request
    massive_keywords = ["print all", "show all", "dump all", "explain every", "everything", "all files", "entire codebase", "every file", "every line"]
    if any(keyword in prompt_lower for keyword in massive_keywords):
        return "requests a massive dump or explanation of the entire codebase. This will blow up the context window and exceed your token budget.", True
        
    # 3. Endless / Redundant Loop request
    loop_keywords = ["forever", "infinite", "loop", "over and over", "repeat"]
    if any(keyword in prompt_lower for keyword in loop_keywords) and ("print" in prompt_lower or "say" in prompt_lower or "run" in prompt_lower):
        return "requests an iterative or infinite repetition of a task, which risks triggering a high-turn agent loop.", True

    return None, False

def main():
    # Read stdin
    input_data = sys.stdin.read() if not sys.stdin.isatty() else ""
    transcript_path = None
    if input_data:
        try:
            data = json.loads(input_data)
            transcript_path = data.get("transcriptPath")
        except Exception:
            pass

    if not transcript_path:
        # Fallback to current dir if not provided
        print(json.dumps({}))
        return

    last_prompt = load_last_user_prompt(transcript_path)
    if not last_prompt:
        print(json.dumps({}))
        return

    warning_reason, is_stupid = analyze_prompt(last_prompt)
    if is_stupid:
        # Construct the injection steps
        inject_steps = [
            {
                "ephemeralMessage": (
                    f"⚠️ [TOKEN-SAVER INTERCEPT]: The user's query ('{last_prompt}') "
                    f"is detected as highly token-inefficient because it {warning_reason}\n\n"
                    "As part of the Token-Saver protocol, you MUST IMMEDIATELY HALT and "
                    "refuse to execute expensive operations (like full codebase reads or broad workspace crawls). "
                    "Respond to the user explaining why their request is extremely expensive in terms of token cost, "
                    "and ask them to narrow down or clarify their requirement."
                )
            }
        ]
        print(json.dumps({"injectSteps": inject_steps}))
    else:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
