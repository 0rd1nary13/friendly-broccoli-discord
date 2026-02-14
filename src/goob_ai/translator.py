"""Gemini translation service."""

from __future__ import annotations

import re

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
        """Translate Chinese source text into configured target language."""
        clean_text: str = source_text.strip()
        if not clean_text:
            return ""
        if not _contains_chinese_text(clean_text):
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
        """Build a deterministic prompt for clean article-body translation."""
        return (
            "Translate the following Chinese text into "
            f"{self._target_language}. Keep facts, numbers, links, and line breaks.\n"
            "Remove signatures, bylines, hashtags, source credits, and other "
            "non-article metadata. Return only the translated article body.\n\n"
            f"{source_text}"
        )


def _contains_chinese_text(text: str) -> bool:
    """Return True when text contains CJK Unified Ideographs."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))
