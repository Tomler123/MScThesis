"""
llm_judge.py — LLM-as-a-Judge Evaluation using Groq (Free Tier)

Sends the original prompt, source text, and model response to Groq's
Llama model for qualitative evaluation across five dimensions:
  1. Faithfulness   — does the summary only contain source info?
  2. Constraint Following — how well were prompt instructions obeyed?
  3. Completeness   — are the key points from the source covered?
  4. Clarity        — is the summary clear and well-written?
  5. Conciseness    — is the summary appropriately brief?

Returns structured JSON scores (1–10) plus textual rationale.
"""

import json
import re
import requests


def evaluate_with_gemini(api_key: str, prompt: str, source: str,
                         response: str, model_name: str = 'Model') -> dict:
    """
    Call Groq API to evaluate a model's summary.
    Function name kept as evaluate_with_gemini for backward compatibility.

    Parameters
    ----------
    api_key : str      – Groq API key (free tier)
    prompt : str       – The original evaluation prompt with constraints
    source : str       – The source text that was summarized
    response : str     – The model's summary output
    model_name : str   – Name of the model being evaluated

    Returns
    -------
    dict with scores and rationale, or error info.
    """
    if not api_key or not api_key.strip():
        return {
            'error': 'No API key provided',
            'scores': _empty_scores()
        }

    judge_prompt = f"""You are an expert NLP evaluator. Your task is to evaluate the quality of an AI model's text summary.

## ORIGINAL PROMPT (given to the AI model):
{prompt}

## SOURCE TEXT (the text to be summarized):
{source[:3000]}

## MODEL RESPONSE ({model_name}):
{response}

## YOUR TASK:
Evaluate the model's response on EXACTLY these 5 dimensions. Score each 1–10.

1. **Faithfulness** (1-10): Does the summary only contain information from the source? No hallucinations or invented facts?
2. **Constraint_Following** (1-10): How well did the model follow the specific structural instructions in the prompt (bullet counts, word limits, section requirements, ordering)?
3. **Completeness** (1-10): Does the summary capture the key points and main ideas from the source?
4. **Clarity** (1-10): Is the summary well-written, clear, and easy to understand?
5. **Conciseness** (1-10): Is the summary appropriately concise without being too short or too verbose?

RESPOND IN EXACTLY THIS JSON FORMAT AND NOTHING ELSE:
{{
    "faithfulness": {{"score": <int>, "rationale": "<1-2 sentences>"}},
    "constraint_following": {{"score": <int>, "rationale": "<1-2 sentences>"}},
    "completeness": {{"score": <int>, "rationale": "<1-2 sentences>"}},
    "clarity": {{"score": <int>, "rationale": "<1-2 sentences>"}},
    "conciseness": {{"score": <int>, "rationale": "<1-2 sentences>"}},
    "overall_comment": "<1-2 sentence overall assessment>"
}}"""

    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key.strip()}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [
                    {'role': 'system', 'content': 'You are an expert NLP evaluator. Always respond with valid JSON only, no markdown fences.'},
                    {'role': 'user', 'content': judge_prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 1000,
            },
            timeout=30,
        )

        if resp.status_code != 200:
            return {
                'error': f'Groq API error: {resp.status_code} {resp.text[:300]}',
                'scores': _empty_scores()
            }

        data = resp.json()
        raw_text = data['choices'][0]['message']['content'].strip()

        # Parse JSON from response (handle markdown code fences)
        raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$', '', raw_text)
        parsed = json.loads(raw_text)

        # Extract scores
        dimensions = ['faithfulness', 'constraint_following', 'completeness',
                      'clarity', 'conciseness']
        scores = {}
        rationales = {}
        for dim in dimensions:
            entry = parsed.get(dim, {})
            scores[dim] = int(entry.get('score', 0))
            rationales[dim] = entry.get('rationale', '')

        scores['average'] = round(sum(scores[d] for d in dimensions) / len(dimensions), 2)

        return {
            'scores': scores,
            'rationales': rationales,
            'overall_comment': parsed.get('overall_comment', ''),
            'error': None
        }

    except json.JSONDecodeError as e:
        return {
            'error': f'Failed to parse response as JSON: {str(e)}',
            'raw_response': raw_text if 'raw_text' in dir() else '',
            'scores': _empty_scores()
        }
    except Exception as e:
        return {
            'error': f'Groq API error: {str(e)}',
            'scores': _empty_scores()
        }


def _empty_scores() -> dict:
    """Return zeroed scores dict."""
    return {
        'faithfulness': 0, 'constraint_following': 0,
        'completeness': 0, 'clarity': 0, 'conciseness': 0,
        'average': 0
    }