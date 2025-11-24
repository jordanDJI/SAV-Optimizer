# backend/data_pipeline/llm_client.py

from __future__ import annotations

import json
from typing import Any, Dict

from mistralai import Mistral  # lib mistralai >= 1.9.0

from backend.config import MISTRAL_API_KEY, MISTRAL_MODEL


class MistralLLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or MISTRAL_API_KEY
        self.model = model or MISTRAL_MODEL
        self.client = Mistral(api_key=self.api_key)

    def classify_tweet(self, text: str) -> Dict[str, Any]:
        system_prompt = (
            "Tu es un assistant pour le service client d'un opérateur télécom (Free/Freebox). "
            "Tu dois classifier des tweets clients avec des catégories métier précises."
        )

        user_prompt = f"""
Analyse le tweet suivant et réponds STRICTEMENT au format JSON :

TWEET:
{text}

1/ intent :
- complaint
- suggestion
- thanks
- question
- praise
- spam_or_irrelevant
- other

2/ complaint_type :
- Si intent != "complaint", mets "none".
- Sinon, choisis parmi :
  - network_outage
  - slow_connection
  - mobile_issue
  - fiber_issue
  - tv_service_issue
  - billing_issue
  - customer_service_issue
  - account_contract_issue
  - equipment_issue
  - other_complaint

3/ sentiment :
- negative
- neutral
- positive

4/ sarcasm :
- true ou false

5/ priority :
- Si intent != "complaint", mets "none".
- Sinon choisis parmi :
  - low
  - medium
  - high
  - critical

Retourne STRICTEMENT un JSON :
{{
  "intent": "...",
  "complaint_type": "...",
  "sentiment": "...",
  "sarcasm": true/false,
  "priority": "...",
  "explanation": "phrase courte expliquant ton choix"
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        resp = self.client.chat.complete(
            model=self.model,
            messages=messages,
            temperature=0.1,
        )
        content = resp.choices[0].message.content

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            try:
                start = content.index("{")
                end = content.rindex("}") + 1
                json_str = content[start:end]
                result = json.loads(json_str)
            except Exception:
                result = {
                    "intent": "other",
                    "complaint_type": "none",
                    "sentiment": "neutral",
                    "sarcasm": False,
                    "priority": "none",
                    "explanation": f"Parsing JSON échoué. Réponse brute: {content[:120]}...",
                }

        return result


_llm_client: MistralLLMClient | None = None


def get_llm_client() -> MistralLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = MistralLLMClient()
    return _llm_client
