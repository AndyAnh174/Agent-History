from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict

import httpx
from loguru import logger


class GeminiService:
    """Thin HTTP client for Gemini 2.0 Flash API."""

    def __init__(self, api_key: str, api_url: str, timeout: float = 40.0):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required.")
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    async def generate_text(self, prompt: str, system_instruction: str | None = None, max_retries: int = 3) -> str:
        contents = [{"parts": [{"text": prompt}]}]
        
        # Build request payload
        payload = {"contents": contents}
        
        # Add system instruction if provided (Gemini API format)
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Gemini API uses query parameter for API key
        url = f"{self.api_url}?key={self.api_key}"
        
        logger.debug(f"Calling Gemini API: {self.api_url} with model key")

        last_error = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        headers={
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    
                    # Log response for debugging
                    if response.status_code != 200:
                        logger.warning(f"Gemini API response: {response.status_code} - {response.text[:200]}")
                    
                    # Handle rate limiting with exponential backoff
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + (attempt * 0.5)  # Exponential backoff: 1s, 2.5s, 5s
                            logger.warning(f"Rate limited (429), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Check if there's a Retry-After header
                            retry_after = response.headers.get("Retry-After", "60")
                            raise ValueError(
                                f"Gemini API rate limit exceeded. Please wait {retry_after} seconds and try again. "
                                "You may have exceeded your API quota or made too many requests too quickly."
                            )
                    
                    response.raise_for_status()
                    data = response.json()

                for candidate in data.get("candidates", []):
                    parts = candidate.get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                raise ValueError("Gemini API returned no candidates.")
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (attempt * 0.5)
                    logger.warning(f"Rate limited (429), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    last_error = e
                    continue
                elif e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After", "60")
                    error_text = e.response.text[:500] if e.response.text else "No error details"
                    logger.error(f"Gemini API 429 error details: {error_text}")
                    raise ValueError(
                        f"Gemini API rate limit exceeded. Please wait {retry_after} seconds and try again. "
                        "You may have exceeded your API quota or made too many requests too quickly."
                    )
                elif e.response.status_code == 400:
                    error_text = e.response.text[:500] if e.response.text else "No error details"
                    logger.error(f"Gemini API 400 error: {error_text}")
                    raise ValueError(f"Gemini API bad request: {error_text}")
                elif e.response.status_code == 401:
                    raise ValueError("Gemini API authentication failed. Please check your API key.")
                elif e.response.status_code == 403:
                    raise ValueError("Gemini API access forbidden. Please check your API key permissions.")
                else:
                    error_text = e.response.text[:500] if e.response.text else "No error details"
                    logger.error(f"Gemini API error {e.response.status_code}: {error_text}")
                    raise ValueError(f"Gemini API error: {e.response.status_code} - {error_text}")
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    logger.warning(f"Request timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                raise ValueError("Gemini API request timeout. Please try again.")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(wait_time)
                    last_error = e
                    continue
                raise
        
        if last_error:
            raise ValueError(f"Gemini API error after {max_retries} attempts: {str(last_error)}")
        raise ValueError("Gemini API request failed")

    async def generate_json(self, prompt: str, system_instruction: str | None = None) -> Dict[str, Any]:
        raw_text = await self.generate_text(prompt, system_instruction=system_instruction)
        json_str = self._extract_json_blob(raw_text)
        return json.loads(json_str)

    async def generate_image(
        self, 
        prompt: str, 
        image_model: str = "gemini-2.0-flash-preview-image-generation",
        max_retries: int = 3
    ) -> str:
        """
        Generate an image using Gemini Image Generation API.
        Returns base64 encoded image data or image URL.
        """
        from ..utils.prompt_validator import PromptValidator
        
        # Validate prompt first
        is_valid, error_msg = PromptValidator.validate_prompt(prompt)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Enhance prompt with safety and educational instructions
        enhanced_prompt = PromptValidator.enhance_prompt(prompt)
        
        contents = [{"parts": [{"text": enhanced_prompt}]}]
        
        # Build request payload for image generation
        # Note: Gemini Image API requires both TEXT and IMAGE modalities
        # Add safety instruction
        safety_instruction = PromptValidator.add_safety_instruction()
        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": safety_instruction}]
            },
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
        }
        
        # Use image generation model URL
        image_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{image_model}:generateContent"
        url = f"{image_api_url}?key={self.api_key}"
        
        logger.debug(f"Calling Gemini Image Generation API: {image_model}")
        
        last_error = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout * 2) as client:  # Longer timeout for image generation
                    response = await client.post(
                        url,
                        headers={
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    
                    # Log response for debugging
                    if response.status_code != 200:
                        logger.warning(f"Gemini Image API response: {response.status_code} - {response.text[:200]}")
                    
                    # Handle rate limiting with exponential backoff
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + (attempt * 0.5)
                            logger.warning(f"Rate limited (429), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            retry_after = response.headers.get("Retry-After", "60")
                            raise ValueError(
                                f"Gemini Image API rate limit exceeded. Please wait {retry_after} seconds and try again."
                            )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract image data from response
                    for candidate in data.get("candidates", []):
                        parts = candidate.get("content", {}).get("parts", [])
                        for part in parts:
                            # Check for inline data (base64) - try both camelCase and snake_case
                            if "inlineData" in part:
                                mime_type = part["inlineData"].get("mimeType", "image/png")
                                image_data = part["inlineData"].get("data", "")
                                if image_data:
                                    # Return data URI for easy display
                                    return f"data:{mime_type};base64,{image_data}"
                            elif "inline_data" in part:
                                mime_type = part["inline_data"].get("mime_type", "image/png")
                                image_data = part["inline_data"].get("data", "")
                                if image_data:
                                    return f"data:{mime_type};base64,{image_data}"
                            # Check for URL
                            elif "url" in part:
                                return part["url"]
                            # Check for image data directly
                            elif "image" in part:
                                image_obj = part.get("image", {})
                                if "data" in image_obj:
                                    mime_type = image_obj.get("mimeType", image_obj.get("mime_type", "image/png"))
                                    image_data = image_obj.get("data", "")
                                    if image_data:
                                        return f"data:{mime_type};base64,{image_data}"
                    
                    # Log full response for debugging if no image found
                    logger.warning(f"Gemini Image API response structure: {json.dumps(data, indent=2)[:500]}")
                    raise ValueError("Gemini Image API returned no image data.")
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (attempt * 0.5)
                    logger.warning(f"Rate limited (429), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    last_error = e
                    continue
                elif e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After", "60")
                    error_text = e.response.text[:500] if e.response.text else "No error details"
                    logger.error(f"Gemini Image API 429 error details: {error_text}")
                    raise ValueError(
                        f"Gemini Image API rate limit exceeded. Please wait {retry_after} seconds and try again."
                    )
                elif e.response.status_code == 400:
                    error_text = e.response.text[:500] if e.response.text else "No error details"
                    logger.error(f"Gemini Image API 400 error: {error_text}")
                    raise ValueError(f"Gemini Image API bad request: {error_text}")
                elif e.response.status_code == 401:
                    raise ValueError("Gemini Image API authentication failed. Please check your API key.")
                elif e.response.status_code == 403:
                    raise ValueError("Gemini Image API access forbidden. Please check your API key permissions.")
                else:
                    error_text = e.response.text[:500] if e.response.text else "No error details"
                    logger.error(f"Gemini Image API error {e.response.status_code}: {error_text}")
                    raise ValueError(f"Gemini Image API error: {e.response.status_code} - {error_text}")
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    logger.warning(f"Request timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                raise ValueError("Gemini Image API request timeout. Please try again.")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(wait_time)
                    last_error = e
                    continue
                raise
        
        if last_error:
            raise ValueError(f"Gemini Image API error after {max_retries} attempts: {str(last_error)}")
        raise ValueError("Gemini Image API request failed")

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
