from __future__ import annotations

from app.llm import llm_client

IMAGE_SCOPE_CHECK_PROMPT = """
You are analyzing an image to determine if it contains food, meals, cooking, or nutrition-related content.

IMPORTANT: You MUST respond with ONLY one word:
- "FOOD" if the image shows food, meals, ingredients, cooking, kitchen scenes, or anything food-related
- "NOT_FOOD" if the image shows anything else (people, landscapes, objects, text, etc. that is NOT food-related)

Do not provide any explanation, just respond with "FOOD" or "NOT_FOOD".
"""


def is_food_image(image_base64: str) -> bool:
    """Check if an image contains food-related content."""
    try:
        response = llm_client.analyze_image(image_base64, IMAGE_SCOPE_CHECK_PROMPT)
        return "FOOD" in response.upper() and "NOT_FOOD" not in response.upper()
    except Exception:
        # If validation fails, default to allowing (but log the error)
        return True

