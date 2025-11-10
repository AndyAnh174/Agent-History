from __future__ import annotations

import json
import re
from typing import Any, Dict

import httpx


class GeminiService:
    """Thin HTTP client for Gemini 2.0 Flash API."""

    def __init__(self, api_key: str, api_url: str, timeout: float = 40.0):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required.")
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    async def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        contents = [{"parts": [{"text": prompt}]}]
        if system_instruction:
            contents.insert(0, {"role": "user", "parts": [{"text": system_instruction}]})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"contents": contents},
            )
            response.raise_for_status()
            data = response.json()

        for candidate in data.get("candidates", []):
            parts = candidate.get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
        raise ValueError("Gemini API returned no candidates.")

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        raw_text = await self.generate_text(prompt)
        json_str = self._extract_json_blob(raw_text)
        return json.loads(json_str)

    @staticmethod
    def _extract_json_blob(text: str) -> str:
        """Extract the first JSON object or array inside the LLM response."""
        text = text.strip()
        if text.startswith("{") or text.startswith("["):
            return text
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if not match:
            raise ValueError("Gemini response did not contain JSON content.")
        return match.group(1)
