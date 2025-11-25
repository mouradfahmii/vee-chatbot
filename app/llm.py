from __future__ import annotations

from typing import Any, List, Mapping, Optional

from litellm import completion

from app.config import settings


class LLMClient:
    """Thin wrapper around LiteLLM to keep provider details localized."""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> None:
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.temperature
        self.api_key = api_key or settings.llm_api_key
        self.api_base = api_base or settings.llm_api_base

    def chat(self, messages: List[Mapping[str, Any]]) -> str:
        kwargs = {"model": self.model, "messages": messages, "temperature": self.temperature}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        response = completion(**kwargs)
        if not response or "choices" not in response:
            raise RuntimeError("No response from language model")
        return response["choices"][0]["message"]["content"].strip()

    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        model: Optional[str] = None,
    ) -> str:
        """Analyze an image using vision model."""
        vision_model = model or settings.vision_model
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ],
            }
        ]
        
        kwargs = {"model": vision_model, "messages": messages, "temperature": self.temperature}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        response = completion(**kwargs)
        if not response or "choices" not in response:
            raise RuntimeError("No response from vision model")
        return response["choices"][0]["message"]["content"].strip()


llm_client = LLMClient()
