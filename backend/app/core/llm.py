import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI


class OpenAILLM:
    """
    OpenAI LLM client for code generation.
    
    Provides dependency injection for model configuration and easier testing.
    """
    
    # Default system prompt (fallback if no prompt_template.txt found)
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
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", 
                 prompt_template_path: Optional[str] = None, temperature: float = 0.0, 
                 max_tokens: int = 1200):
        """
        Initialize OpenAI LLM client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use
            prompt_template_path: Path to custom prompt template
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
        """
        load_dotenv()
        
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Set up prompt template path
        if prompt_template_path:
            self.prompt_template_path = prompt_template_path
        else:
            # Default path: backend/app/core/llm.py -> ../../prompt_template.txt
            self.prompt_template_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "prompt_template.txt"
            )
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from template file or use default."""
        if os.path.exists(self.prompt_template_path):
            with open(self.prompt_template_path, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
            print(f"[LLM] Using system prompt from: {self.prompt_template_path}")
            return prompt
        print("[LLM] Using built-in default system prompt.")
        return self.DEFAULT_SYSTEM
    
    def build_messages(self, problem_text: str, examples: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, str]]:
        """Build messages for OpenAI chat model."""
        system = self._load_system_prompt()
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
    
    def generate_code(self, problem_text: str, examples: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate Python code for the given problem.
        
        Args:
            problem_text: Description of the coding problem
            examples: List of example test cases
            
        Returns:
            Generated Python code
        """
        messages = self.build_messages(problem_text, examples)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        content = response.choices[0].message.content
        return self._extract_code(content)
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from LLM output."""
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


# Backward compatibility functions
def call_llm(problem_text: str, examples: Optional[List[Dict[str, Any]]] = None) -> str:
    """Backward compatibility function."""
    llm = OpenAILLM()
    return llm.generate_code(problem_text, examples)


def build_messages(problem_text: str, examples: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, str]]:
    """Backward compatibility function."""
    llm = OpenAILLM()
    return llm.build_messages(problem_text, examples)
