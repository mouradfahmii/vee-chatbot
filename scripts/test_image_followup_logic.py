#!/usr/bin/env python3
"""Test script to verify image follow-up context logic (standalone, no dependencies)."""

import sys
import re
from typing import Sequence

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# Copy the relevant logic from FoodChatbot for testing
FOOD_KEYWORDS = {
    "cook", "recipe", "meal", "food", "dinner", "lunch", "breakfast", "snack",
    "ingredient", "calorie", "calories", "nutrition", "diet", "prep", "preparation",
    "kitchen", "bake", "roast", "grill", "fry", "steam", "boil", "sauté",
    "protein", "carb", "fat", "macro", "serving", "portion", "dietary",
    "allergy", "vegetarian", "vegan", "pescatarian", "gluten", "dairy",
    "session", "chef", "cooking class", "meal plan", "prep time", "cook time",
    "calculate", "track", "photo", "upload", "estimate"
}


def is_food_related(query: str, history: Sequence[dict] | None = None) -> bool:
    """
    Check if query is related to food/cooking topics.
    
    Args:
        query: The user's question or message
        history: Optional conversation history to check for context (e.g., recent image analysis)
    
    Returns:
        True if the query is food-related, False otherwise
    """
    # Normalize query: remove punctuation and extra spaces for better matching
    query_normalized = re.sub(r'[^\w\s]', '', query.lower())
    query_normalized = ' '.join(query_normalized.split())
    # Check if any keyword appears in the normalized query
    if any(keyword in query_normalized for keyword in FOOD_KEYWORDS):
        return True
    
    # Check if this is a follow-up to image analysis
    # If history exists and contains recent image analysis, treat follow-up questions as food-related
    if history:
        # Check only the most recent 2 turns to see if there was an image analysis
        # This ensures immediate follow-up questions after image uploads are treated as food-related
        # but prevents old image analyses from affecting unrelated questions
        for turn in reversed(history[-2:]):  # Check most recent 2 turns only
            if turn.get('user', '').startswith('[IMAGE]'):
                # This is a follow-up to image analysis - treat as food-related
                return True
    
    return False


def test_is_food_related_with_history():
    """Test is_food_related() method with conversation history."""
    print("=" * 80)
    print("TESTING: is_food_related() with conversation history")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        {
            "name": "Follow-up after image (no keywords)",
            "question": "what about the calories?",
            "history": [
                {"user": "[IMAGE] What is in this image? Estimate the calories.", "assistant": "This image shows a plate of pasta..."}
            ],
            "expected": True,
            "description": "Should be True because it's a follow-up to image analysis"
        },
        {
            "name": "Follow-up after image (generic)",
            "question": "tell me more",
            "history": [
                {"user": "[IMAGE] What is in this image?", "assistant": "This image shows..."}
            ],
            "expected": True,
            "description": "Should be True because it's a follow-up to image analysis"
        },
        {
            "name": "Follow-up after image (very short)",
            "question": "what else?",
            "history": [
                {"user": "[IMAGE] Analyze this image", "assistant": "The image contains..."}
            ],
            "expected": True,
            "description": "Should be True because it's a follow-up to image analysis"
        },
        {
            "name": "Question with food keywords (no history)",
            "question": "how many calories in pasta?",
            "history": None,
            "expected": True,
            "description": "Should be True because it contains food keywords"
        },
        {
            "name": "Non-food question (no history, no image)",
            "question": "what's the weather today?",
            "history": None,
            "expected": False,
            "description": "Should be False - not food-related and no image context"
        },
        {
            "name": "Non-food question (with old image history)",
            "question": "what's the weather today?",
            "history": [
                {"user": "How do I cook pasta?", "assistant": "To cook pasta..."},
                {"user": "[IMAGE] What is in this image?", "assistant": "This image shows..."},
                {"user": "How do I cook pasta?", "assistant": "To cook pasta..."},
                {"user": "How do I cook pasta?", "assistant": "To cook pasta..."},
            ],
            "expected": False,
            "description": "Should be False - old image history (beyond last 2 turns) shouldn't affect non-food questions"
        },
        {
            "name": "Follow-up after recent image (within last 2 turns)",
            "question": "can you give me more details?",
            "history": [
                {"user": "How do I cook pasta?", "assistant": "To cook pasta..."},
                {"user": "[IMAGE] What is in this image?", "assistant": "This image shows..."},
                {"user": "tell me more", "assistant": "More details..."}
            ],
            "expected": True,
            "description": "Should be True - recent image in history (within last 2 turns)"
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Question: '{test_case['question']}'")
        print(f"History: {len(test_case['history']) if test_case['history'] else 0} turns")
        if test_case['history']:
            print(f"  Last user message: {test_case['history'][-1]['user'][:60]}...")
        print(f"Expected: {test_case['expected']}")
        print(f"Description: {test_case['description']}")
        
        result = is_food_related(test_case['question'], history=test_case['history'])
        print(f"Result: {result}")
        
        if result == test_case['expected']:
            print("✓ PASSED")
            passed += 1
        else:
            print(f"✗ FAILED - Expected {test_case['expected']}, got {result}")
            failed += 1
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return False


def test_conversation_flow():
    """Test a simulated conversation flow."""
    print("\n" + "=" * 80)
    print("TESTING: Simulated Conversation Flow")
    print("=" * 80)
    
    history = []
    
    # Step 1: Image upload
    print("\n[Step 1] User uploads image")
    image_question = "[IMAGE] What is in this image? Estimate the calories."
    image_answer = "This image shows a delicious plate of pasta with marinara sauce. Estimated calories: 450-500."
    history.append({"user": image_question, "assistant": image_answer})
    print(f"  User: {image_question}")
    print(f"  Vee: {image_answer}")
    
    # Step 2: Follow-up question
    print("\n[Step 2] User asks follow-up (no food keywords)")
    followup = "what about the calories?"
    is_food = is_food_related(followup, history=history)
    print(f"  User: {followup}")
    print(f"  is_food_related('{followup}', history): {is_food}")
    
    if is_food:
        print("  ✓ SUCCESS: Follow-up question correctly identified as food-related!")
        print("  → This means the context fix is working!")
    else:
        print("  ✗ FAILED: Follow-up question NOT identified as food-related")
        print("  → This means the context fix is NOT working!")
        return False
    
    # Step 3: Another follow-up
    print("\n[Step 3] User asks another follow-up (very generic)")
    followup2 = "tell me more"
    is_food2 = is_food_related(followup2, history=history)
    print(f"  User: {followup2}")
    print(f"  is_food_related('{followup2}', history): {is_food2}")
    
    if is_food2:
        print("  ✓ SUCCESS: Generic follow-up correctly identified as food-related!")
    else:
        print("  ✗ FAILED: Generic follow-up NOT identified as food-related")
        return False
    
    # Step 4: Non-food question (after more conversation, image should be out of context)
    print("\n[Step 4] User asks non-food question (after more conversation)")
    # Add more conversation turns to push image out of last 2 turns
    history.append({"user": "How do I cook pasta?", "assistant": "To cook pasta, boil water..."})
    history.append({"user": "What's a good recipe?", "assistant": "Here's a great recipe..."})
    
    non_food = "what's the weather today?"
    is_food3 = is_food_related(non_food, history=history)
    print(f"  User: {non_food}")
    print(f"  History now has {len(history)} turns (image should be beyond last 2 turns)")
    print(f"  is_food_related('{non_food}', history): {is_food3}")
    
    if not is_food3:
        print("  ✓ SUCCESS: Non-food question correctly rejected when image is out of context!")
    else:
        print("  ✗ FAILED: Non-food question incorrectly identified as food-related")
        return False
    
    return True


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print("IMAGE FOLLOW-UP CONTEXT LOGIC TEST")
    print("=" * 80)
    print("\nThis test verifies that is_food_related() correctly identifies")
    print("follow-up questions after image uploads as food-related.")
    print("\nNote: This test does NOT require LLM API access or dependencies.")
    
    # Run tests
    test1_passed = test_is_food_related_with_history()
    test2_passed = test_conversation_flow()
    
    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    if test1_passed and test2_passed:
        print("✓ ALL TESTS PASSED - Image follow-up context is working correctly!")
        print("\nThe fix is working! Follow-up questions after image uploads")
        print("will now be correctly identified as food-related.")
    else:
        print("✗ SOME TESTS FAILED - Please review the output above")
    print("=" * 80)
