#!/usr/bin/env python3
"""Test image analysis functionality."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.chatbot import bot
from app.image_utils import encode_image_to_base64


def test_image_analysis(image_path: str) -> None:
    """Test image analysis with the chatbot."""
    print(f"Testing image analysis with: {image_path}")
    print("=" * 80)
    
    # Test 1: General question
    print("\n[Test 1] General question about the image")
    print("Q: What is in this image?")
    answer1 = bot.answer_with_image(image_path, question="What is in this image?")
    print(f"A: {answer1}\n")
    
    # Test 2: Calorie-specific question
    print("\n[Test 2] Calorie estimation")
    print("Q: How many calories are in this meal?")
    answer2 = bot.answer_with_image(
        image_path, question="How many calories are in this meal? Estimate the calories."
    )
    print(f"A: {answer2}\n")
    
    # Test 3: Ingredients question
    print("\n[Test 3] Ingredients identification")
    print("Q: What ingredients can you identify?")
    answer3 = bot.answer_with_image(
        image_path, question="What ingredients can you identify in this meal?"
    )
    print(f"A: {answer3}\n")
    
    print("=" * 80)
    print("Image analysis tests complete!")


if __name__ == "__main__":
    # Generate test image if it doesn't exist
    test_image_path = Path(__file__).parent.parent / "test_images" / "test_meal.jpg"
    
    if not test_image_path.exists():
        print("Generating test meal image...")
        import subprocess
        
        subprocess.run(
            ["python", str(Path(__file__).parent / "generate_test_meal.py")],
            check=True,
        )
    
    if test_image_path.exists():
        test_image_analysis(str(test_image_path))
    else:
        print(f"Error: Test image not found at {test_image_path}")
        sys.exit(1)

