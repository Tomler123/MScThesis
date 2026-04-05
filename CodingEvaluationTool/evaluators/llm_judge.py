"""
LLM-as-Judge for Code Evaluation
=================================
Uses Groq API (Llama 3.3 70B) for qualitative code evaluation.
Function named evaluate_with_gemini for backward compatibility
but actually calls Groq.
"""

import json
import requests
from typing import Optional


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert code reviewer and evaluator for an academic research project comparing AI coding assistants. 

You will receive:
1. The original prompt/task given to AI models
2. A model's code response
3. Optionally, a reference/correct solution

Evaluate the code on these dimensions (score each 1-10):

1. **Correctness** — Does the code solve the problem correctly? Does it handle all specified requirements?
2. **Completeness** — Does it address ALL constraints in the prompt? Missing any requirements?
3. **Code Quality** — Readability, naming, structure, Pythonic idioms, clean code principles.
4. **Edge Case Handling** — Does it handle boundary conditions, empty inputs, invalid data?
5. **Documentation** — Quality of docstrings, comments, type hints. Are they helpful and accurate?
6. **Efficiency** — Is the algorithm efficient? Any unnecessary work or suboptimal approaches?
7. **Error Handling** — Proper use of exceptions, input validation, graceful failure.
8. **Adherence to Constraints** — How closely does it follow the specific constraints in the prompt?

Respond in this exact JSON format (NO markdown, NO code fences):
{
    "scores": {
        "correctness": <1-10>,
        "completeness": <1-10>,
        "code_quality": <1-10>,
        "edge_case_handling": <1-10>,
        "documentation": <1-10>,
        "efficiency": <1-10>,
        "error_handling": <1-10>,
        "constraint_adherence": <1-10>
    },
    "overall_score": <1-10>,
    "summary": "<2-3 sentence summary>",
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
    "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
}
"""


def evaluate_with_gemini(
    prompt: str,
    code: str,
    reference_code: str = "",
    api_key: str = "",
    model_name: str = ""
) -> dict:
    """
    Evaluate code using LLM-as-Judge via Groq API.
    Named evaluate_with_gemini for backward compatibility but uses Groq (Llama 3.3 70B).

    Args:
        prompt: The original task/prompt given to AI models
        code: The model's code response
        reference_code: Optional reference/correct solution
        api_key: Groq API key (starts with gsk_)
        model_name: Name of the model being evaluated (for context)

    Returns:
        Dict with evaluation scores and feedback
    """
    if not api_key:
        return {"error": "No API key provided. Enter your Groq API key (starts with gsk_)."}

    if not api_key.startswith("gsk_"):
        return {"error": "Invalid API key format. Groq keys start with 'gsk_'."}

    # Build the evaluation message
    user_message = f"""## Task Prompt
{prompt}

## Model Being Evaluated: {model_name or 'Unknown'}

## Model's Code Response
```python
{code}
```
"""

    if reference_code.strip():
        user_message += f"""
## Reference/Correct Solution
```python
{reference_code}
```
"""

    user_message += """
Please evaluate the model's code response against the task prompt. Score each dimension 1-10 and provide structured feedback. Respond with ONLY the JSON object, no additional text or markdown formatting."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 401:
            return {"error": "Authentication failed. Check your Groq API key."}
        elif response.status_code == 429:
            return {"error": "Rate limit exceeded. Please wait a moment and try again."}
        elif response.status_code != 200:
            return {"error": f"Groq API returned status {response.status_code}: {response.text[:200]}"}

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Clean up response — strip markdown fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)

        # Validate structure
        if "scores" not in result or "overall_score" not in result:
            return {"error": "LLM returned invalid format. Missing 'scores' or 'overall_score'."}

        result["model_evaluated"] = model_name
        result["judge_model"] = GROQ_MODEL
        result["provider"] = "Groq"

        return result

    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Groq API did not respond within 30 seconds."}
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to Groq API. Check your internet connection."}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse LLM response as JSON: {str(e)[:100]}"}
    except KeyError as e:
        return {"error": f"Unexpected API response structure: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)[:200]}"}
