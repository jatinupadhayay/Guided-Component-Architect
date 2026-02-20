import json
from generator import ComponentGenerator
from validator import CodeValidator

def orchestrate_agentic_loop(user_prompt, max_retries=3, model_preference="groq", conversation_history=None, api_keys=None):
    generator = ComponentGenerator(model_preference=model_preference, api_keys=api_keys or {})
    validator = CodeValidator(generator.design_system)

    # Build prompt with conversation context
    if conversation_history:
        context = "\n".join([f"Previous: {h}" for h in conversation_history[-3:]])
        full_prompt = f"Context from previous turns:\n{context}\n\nNew request: {user_prompt}"
    else:
        full_prompt = user_prompt

    current_prompt = generator.build_prompt(full_prompt)

    for attempt in range(1, max_retries + 1):
        yield {"step": "attempt", "value": attempt}
        yield {"step": "generating", "value": f"Generating code (Attempt {attempt}/{max_retries})..."}

        raw_output = generator.call_llm(current_prompt)

        yield {"step": "validating", "value": "Validating design compliance & syntax..."}
        errors, code_dict = validator.validate(raw_output)

        if not errors:
            yield {"step": "success", "value": "Validation passed!", "data": code_dict}
            return code_dict

        yield {"step": "failed", "value": f"Found {len(errors)} issue(s)", "errors": errors}

        if attempt < max_retries:
            yield {"step": "correcting", "value": "Re-prompting LLM with error feedback..."}
            tokens = generator.design_system.get("tokens", {})
            current_prompt = f"""The previous Angular component had errors. Fix them.

ERRORS:
{chr(10).join(f'- {e}' for e in errors)}

You MUST use the primary color {tokens.get('primary-color', '#6366f1')} and follow the design system.
Output ONLY valid JSON with keys: "html", "css", "typescript". No markdown.
"""
        else:
            yield {"step": "max_retries", "value": "Max retries reached.", "data": code_dict}
            return code_dict


def main():
    """CLI entry point for testing."""
    print("Initializing Guided Component Architect Agentic Loop...")
    user_request = "A modern login card with a glassmorphism effect, email and password fields."

    for update in orchestrate_agentic_loop(user_request):
        step = update["step"]
        val = update["value"]
        if step == "attempt":
            print(f"\n=== Attempt {val} ===")
        elif step == "failed":
            print(f"FAILED: {val}")
            for err in update.get("errors", []):
                print(f"  - {err}")
        elif step == "success":
            print(f"SUCCESS: {val}")
            print(json.dumps(update["data"], indent=2))
        elif step == "max_retries":
            print(f"WARNING: {val}")
            if update.get("data"):
                print(json.dumps(update["data"], indent=2))
        else:
            print(val)


if __name__ == "__main__":
    main()
