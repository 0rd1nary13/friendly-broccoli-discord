"""Gemini translation service."""

from __future__ import annotations

from google import genai
from google.genai import types

TRANSLATION_SYSTEM_PROMPT: str = (
    "You are a professional translator. Keep facts unchanged, preserve names, "
    "tickers, numbers, links, and formatting. Return translation only."
)


class TranslationService:
    """Translate text using Gemini generate-content API."""

    def __init__(self, api_key: str, model: str, target_language: str) -> None:
        """Initialize translator service with model and target language."""
        self._client: genai.Client = genai.Client(api_key=api_key)
        self._model: str = model
        self._target_language: str = target_language

    async def translate(self, source_text: str) -> str:
        """Translate source text into configured target language."""
        clean_text: str = source_text.strip()
        if not clean_text:
            return ""

        prompt: str = self._build_prompt(clean_text)
        completion = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=TRANSLATION_SYSTEM_PROMPT,
                temperature=0.1,
            ),
        )
        translated: str | None = completion.text
        return translated.strip() if translated else ""

    def _build_prompt(self, source_text: str) -> str:
        """Build a deterministic translation prompt with target language."""
        return (
            f"Translate the following text to {self._target_language}. "
            "Keep structure, line breaks, and emojis.\n\n"
            f"{source_text}"
        )
