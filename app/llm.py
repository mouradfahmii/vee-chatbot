from __future__ import annotations

from typing import Any, List, Mapping, Optional

from litellm import completion
import litellm

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

    def chat(self, messages: List[Mapping[str, Any]], timeout: Optional[int] = None) -> str:
        """
        Send chat messages to the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            timeout: Optional timeout in seconds. If None, uses settings.llm_timeout_seconds
        
        Returns:
            The assistant's response text
            
        Raises:
            TimeoutError: If the LLM call exceeds the timeout
            RuntimeError: If the response is invalid
        """
        timeout_seconds = timeout if timeout is not None else settings.llm_timeout_seconds
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "timeout": timeout_seconds,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        try:
            response = completion(**kwargs)
        except (TimeoutError, litellm.exceptions.Timeout) as e:
            raise TimeoutError(
                f"LLM API call timed out after {timeout_seconds} seconds. "
                "The request took too long to process. Please try again."
            ) from e
        except Exception as e:
            # Re-raise other exceptions with context
            raise RuntimeError(f"Error calling LLM API: {str(e)}") from e
        
        if not response or "choices" not in response:
            raise RuntimeError("No response from language model")
        return response["choices"][0]["message"]["content"].strip()

    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """
        Analyze an image using vision model.
        
        Args:
            image_base64: Base64-encoded image data
            prompt: Text prompt describing what to analyze
            model: Optional vision model override
            timeout: Optional timeout in seconds. If None, uses settings.vision_timeout_seconds
        
        Returns:
            The assistant's analysis text
            
        Raises:
            TimeoutError: If the vision API call exceeds the timeout
            RuntimeError: If the response is invalid
        """
        vision_model = model or settings.vision_model
        timeout_seconds = timeout if timeout is not None else settings.vision_timeout_seconds
        
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
        
        kwargs = {
            "model": vision_model,
            "messages": messages,
            "temperature": self.temperature,
            "timeout": timeout_seconds,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        try:
            response = completion(**kwargs)
        except (TimeoutError, litellm.exceptions.Timeout) as e:
            raise TimeoutError(
                f"Vision API call timed out after {timeout_seconds} seconds. "
                "Image analysis took too long. Please try again with a smaller image or different prompt."
            ) from e
        except Exception as e:
            # Re-raise other exceptions with context
            raise RuntimeError(f"Error calling vision API: {str(e)}") from e
        
        if not response or "choices" not in response:
            raise RuntimeError("No response from vision model")
        return response["choices"][0]["message"]["content"].strip()


llm_client = LLMClient()
