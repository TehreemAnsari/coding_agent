import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------
# Load environment variables (.env)
# ---------------------------------------------------------------------
load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# ---------------------------------------------------------------------
# Default system prompt (fallback if no prompt_template.txt found)
# ---------------------------------------------------------------------
DEFAULT_SYSTEM = (
    "You are a careful Python assistant. Return ONLY valid Python code for a single file.\n"
    "The code must define a top-level function named `solve` that directly matches the test case inputs.\n"
    "Examples:\n"
    "- For [[[1,2],3]] use: def solve(a, b): ...\n"
    "- For [[['hello'],'olleh']] use: def solve(s): ...\n"
    "Do NOT define def solve(inputs) or take a list as one argument unless the input itself is a list.\n"
    "Return results directly, not via print().\n"
    "Use only Python standard library. Avoid side effects or dangerous operations.\n"
    "Do not include explanations, markdown, or text—return pure Python code."
)

# ---------------------------------------------------------------------
# Load prompt_template.txt if available
# ---------------------------------------------------------------------
PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "prompt_template.txt")

def _load_system_prompt() -> str:
    if os.path.exists(PROMPT_TEMPLATE_PATH):
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
        print(f"[LLM] Using system prompt from: {PROMPT_TEMPLATE_PATH}")
        return prompt
    print("[LLM] Using built-in default system prompt.")
    return DEFAULT_SYSTEM

# ---------------------------------------------------------------------
# Build messages for OpenAI chat model
# ---------------------------------------------------------------------
def build_messages(problem_text: str, examples: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, str]]:
    system = _load_system_prompt()
    user = f"""Problem:
{problem_text}

Guidelines:
- Write a function named `solve` whose parameters exactly match the inputs of each test case.
- For test case input like ["hello"], treat the argument as a single string, not a list of strings.
- Do NOT index into parameters unless the problem explicitly requires it.
- Return the result directly (no prints).
- The runner will call your function as solve(*args).
- Use only Python stdlib and avoid any external dependencies.
"""
    if examples:
        user += "\nTest Cases (examples):\n"
        for ex in examples[:5]:
            user += f"- inputs={ex['inputs']}, expected={ex['expected']}\n"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

# ---------------------------------------------------------------------
# Core function to call the OpenAI model
# ---------------------------------------------------------------------
def call_llm(problem_text: str, examples: Optional[List[Dict[str, Any]]] = None) -> str:
    messages = build_messages(problem_text, examples)
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.0,
        max_tokens=1200,
    )
    content = response.choices[0].message.content
    return _extract_code(content)

# ---------------------------------------------------------------------
# Extract Python code from the LLM output
# ---------------------------------------------------------------------
def _extract_code(text: str) -> str:
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        for i, p in enumerate(parts):
            if i % 2 == 1:  # inside a code block
                lines = p.strip().split("\n")
                if lines and lines[0].strip().lower().startswith("python"):
                    return "\n".join(lines[1:]).strip()
                return p.strip()
    return t
