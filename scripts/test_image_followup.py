#!/usr/bin/env python3
"""Test script to verify image follow-up context is working correctly."""

import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.chatbot import bot
from app.conversation_manager import conversation_manager


def simulate_image_upload(conversation_id: str, user_id: str = "test_user") -> str:
    """Simulate an image upload by calling answer_with_image with a test image."""
    print("\n" + "=" * 80)
    print("STEP 1: Upload Image")
    print("=" * 80)
    
    # Create a simple test image (1x1 pixel PNG)
    # In a real scenario, this would be an actual food image
    import base64
    # Minimal valid PNG (1x1 red pixel)
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    question = "What is in this image? Estimate the calories."
    print(f"User (Image Upload): {question}")
    
    try:
        # Decode base64 to bytes
        image_data = base64.b64decode(test_image_base64)
        
        # Analyze image
        answer = bot.answer_with_image(
            image_data,
            question=question,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        print(f"Vee: {answer}")
        
        # Store in conversation manager (this happens in the API endpoint)
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_message=f"[IMAGE] {question}",
            assistant_message=answer,
            user_id=user_id,
        )
        
        print(f"\n✓ Image analyzed and stored in conversation history")
        return answer
    except Exception as e:
        print(f"✗ Error analyzing image: {e}")
        # Still add a mock entry for testing
        mock_answer = "This appears to be a test image. In a real scenario, I would analyze the food items and estimate calories."
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_message=f"[IMAGE] {question}",
            assistant_message=mock_answer,
            user_id=user_id,
        )
        print(f"Vee (Mock): {mock_answer}")
        print(f"\n✓ Mock entry added to conversation history for testing")
        return mock_answer


def test_followup_question(conversation_id: str, question: str, user_id: str = "test_user") -> None:
    """Test a follow-up question after image upload."""
    print("\n" + "=" * 80)
    print(f"STEP 2: Follow-up Question: '{question}'")
    print("=" * 80)
    
    # Get conversation history
    history_turns = conversation_manager.get_history(conversation_id)
    history = [{"user": turn.user, "assistant": turn.assistant} for turn in history_turns]
    
    print(f"Conversation history length: {len(history)}")
    if history:
        print("Recent history:")
        for i, turn in enumerate(history[-2:], 1):  # Show last 2 turns
            print(f"  {i}. User: {turn['user'][:60]}...")
            print(f"     Assistant: {turn['assistant'][:60]}...")
    
    # Check if question would be treated as food-related
    is_food = bot.is_food_related(question, history=history)
    print(f"\n✓ is_food_related(question, history): {is_food}")
    
    if is_food:
        print("  → Question is correctly identified as food-related (follow-up to image)")
    else:
        print("  ✗ Question is NOT identified as food-related (this is a problem!)")
    
    # Get answer
    print(f"\nUser: {question}")
    try:
        answer = bot.answer(
            question,
            history=history if history else None,
            user_id=user_id,
            conversation_id=conversation_id
        )
        print(f"Vee: {answer}")
        
        # Check if answer redirects away from food (bad sign)
        answer_lower = answer.lower()
        redirected = any(phrase in answer_lower for phrase in [
            "i'm vee", "culinary assistant", "food-related", 
            "cooking questions", "can't help", "only help", "only answer"
        ])
        
        if redirected and is_food:
            print("\n⚠ WARNING: Question was identified as food-related but answer redirects!")
            print("  This might indicate an issue with the prompt handling.")
        elif not redirected and is_food:
            print("\n✓ SUCCESS: Question was identified as food-related and answered appropriately!")
        elif redirected and not is_food:
            print("\n✗ FAILED: Question was not identified as food-related and was redirected.")
            print("  This is the bug we're trying to fix!")
        else:
            print("\n? Unexpected state")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run the image follow-up context test."""
    import uuid
    
    print("=" * 80)
    print("IMAGE FOLLOW-UP CONTEXT TEST")
    print("=" * 80)
    print("\nThis test simulates:")
    print("1. User uploads an image")
    print("2. User asks a follow-up question (without food keywords)")
    print("3. Verifies that follow-up is treated as food-related")
    
    conversation_id = str(uuid.uuid4())
    user_id = "test_user"
    
    # Step 1: Simulate image upload
    image_answer = simulate_image_upload(conversation_id, user_id)
    
    # Step 2: Test various follow-up questions
    followup_questions = [
        "what about the calories?",  # No food keywords, but follow-up
        "tell me more",  # Very generic, no keywords
        "how many calories?",  # Has "calories" keyword, should work anyway
        "can you give me more details?",  # Generic follow-up
        "what else?",  # Very short, no keywords
    ]
    
    for question in followup_questions:
        test_followup_question(conversation_id, question, user_id)
    
    # Test a non-food question to ensure it's still rejected
    print("\n" + "=" * 80)
    print("STEP 3: Non-food Question (Should be rejected)")
    print("=" * 80)
    test_followup_question(conversation_id, "What's the weather today?", user_id)
    
    # Cleanup
    conversation_manager.clear_conversation(conversation_id)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

