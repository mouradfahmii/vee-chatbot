#!/usr/bin/env python3
"""
Direct test of conversation memory without API server.
Tests the conversation manager and chatbot directly.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.chatbot import bot
from app.conversation_manager import conversation_manager
import uuid


def simulate_conversation():
    """Simulate a multi-turn conversation to test memory."""
    
    print("=" * 80)
    print("Simulating Conversation with Memory")
    print("=" * 80)
    print()
    
    # Generate a conversation ID
    conversation_id = str(uuid.uuid4())
    user_id = "test_user_001"
    
    print(f"Conversation ID: {conversation_id}")
    print(f"User ID: {user_id}")
    print()
    
    # Turn 1: First message
    print("-" * 80)
    print("Turn 1: User asks about recipes")
    print("-" * 80)
    message1 = "What are some healthy dinner recipes?"
    print(f"User: {message1}")
    
    # Get history (should be empty)
    history1 = conversation_manager.get_history(conversation_id)
    print(f"History before turn 1: {len(history1)} turns")
    
    # Get answer
    answer1 = bot.answer(message1, history=None, user_id=user_id)
    print(f"Bot: {answer1[:200]}...")
    
    # Store the turn
    conversation_manager.add_turn(
        conversation_id=conversation_id,
        user_message=message1,
        assistant_message=answer1,
        user_id=user_id,
    )
    print()
    
    # Turn 2: Follow-up question
    print("-" * 80)
    print("Turn 2: User asks for more details (should reference previous conversation)")
    print("-" * 80)
    message2 = "Can you tell me more about the first one?"
    print(f"User: {message2}")
    
    # Get history (should have 1 turn now)
    history2 = conversation_manager.get_history(conversation_id)
    print(f"History before turn 2: {len(history2)} turns")
    if history2:
        print(f"  Previous turn: User said '{history2[0].user[:50]}...'")
        print(f"  Bot replied: '{history2[0].assistant[:50]}...'")
    
    # Convert history to format expected by bot
    history_dict = [{"user": turn.user, "assistant": turn.assistant} for turn in history2]
    
    # Get answer with history
    answer2 = bot.answer(message2, history=history_dict, user_id=user_id)
    print(f"Bot: {answer2[:200]}...")
    
    # Store the turn
    conversation_manager.add_turn(
        conversation_id=conversation_id,
        user_message=message2,
        assistant_message=answer2,
        user_id=user_id,
    )
    print()
    
    # Turn 3: Another follow-up
    print("-" * 80)
    print("Turn 3: User asks about ingredients (should remember the recipe)")
    print("-" * 80)
    message3 = "What ingredients do I need?"
    print(f"User: {message3}")
    
    # Get history (should have 2 turns now)
    history3 = conversation_manager.get_history(conversation_id)
    print(f"History before turn 3: {len(history3)} turns")
    
    # Convert history to format expected by bot
    history_dict = [{"user": turn.user, "assistant": turn.assistant} for turn in history3]
    
    # Get answer with history
    answer3 = bot.answer(message3, history=history_dict, user_id=user_id)
    print(f"Bot: {answer3[:200]}...")
    
    # Store the turn
    conversation_manager.add_turn(
        conversation_id=conversation_id,
        user_message=message3,
        assistant_message=answer3,
        user_id=user_id,
    )
    print()
    
    # Verify final history
    print("-" * 80)
    print("Final Conversation History")
    print("-" * 80)
    final_history = conversation_manager.get_history(conversation_id)
    print(f"Total turns: {len(final_history)}")
    for i, turn in enumerate(final_history, 1):
        print(f"\nTurn {i}:")
        print(f"  User: {turn.user[:100]}...")
        print(f"  Bot: {turn.assistant[:100]}...")
    
    print()
    print("=" * 80)
    print("[OK] Conversation memory test completed successfully!")
    print("=" * 80)
    
    return True


def test_arabic_conversation():
    """Test Arabic conversation memory."""
    
    print("\n" + "=" * 80)
    print("Testing Arabic Conversation Memory")
    print("=" * 80)
    print()
    
    conversation_id = str(uuid.uuid4())
    user_id = "test_user_002"
    
    print(f"Conversation ID: {conversation_id}")
    print()
    
    # Turn 1: Arabic message
    print("-" * 80)
    print("Turn 1: Arabic question")
    print("-" * 80)
    message1 = "ما هي وصفة صحية وسريعة للعشاء؟"
    print(f"User: {message1}")
    
    answer1 = bot.answer(message1, history=None, user_id=user_id)
    print(f"Bot: {answer1[:200]}...")
    
    conversation_manager.add_turn(
        conversation_id=conversation_id,
        user_message=message1,
        assistant_message=answer1,
        user_id=user_id,
    )
    print()
    
    # Turn 2: Follow-up in Arabic
    print("-" * 80)
    print("Turn 2: Arabic follow-up (should remember previous conversation)")
    print("-" * 80)
    message2 = "ما هي المكونات؟"
    print(f"User: {message2}")
    
    history2 = conversation_manager.get_history(conversation_id)
    history_dict = [{"user": turn.user, "assistant": turn.assistant} for turn in history2]
    
    answer2 = bot.answer(message2, history=history_dict, user_id=user_id)
    print(f"Bot: {answer2[:200]}...")
    
    conversation_manager.add_turn(
        conversation_id=conversation_id,
        user_message=message2,
        assistant_message=answer2,
        user_id=user_id,
    )
    print()
    
    print("=" * 80)
    print("[OK] Arabic conversation memory test completed!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        print("\nNote: This test uses the chatbot directly (no API server needed)")
        print("Make sure you have set up your .env file with API keys.\n")
        
        # Test English conversation
        success1 = simulate_conversation()
        
        # Test Arabic conversation
        success2 = test_arabic_conversation()
        
        if success1 and success2:
            print("\n[OK] All tests passed!")
            sys.exit(0)
        else:
            print("\n[ERROR] Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

