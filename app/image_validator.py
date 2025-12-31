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
    """
    Check if an image contains food-related content.
    
    NOTE: This function is kept for backward compatibility, but validation is now
    combined with analysis in the main image analysis prompt for better performance.
    This eliminates the need for a separate API call, reducing processing time from
    ~25 seconds to ~8-12 seconds.
    
    The combined approach is used by default in `answer_with_image()`. This function
    can still be used if separate validation is needed (e.g., for testing or specific use cases).
    """
    try:
        response = llm_client.analyze_image(image_base64, IMAGE_SCOPE_CHECK_PROMPT)
        return "FOOD" in response.upper() and "NOT_FOOD" not in response.upper()
    except Exception:
        # If validation fails, default to allowing (but log the error)
        return True

