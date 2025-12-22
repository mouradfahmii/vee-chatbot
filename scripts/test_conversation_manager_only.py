#!/usr/bin/env python3
"""
Test conversation manager directly without requiring chatbot dependencies.
This tests the core conversation memory functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.conversation_manager import ConversationManager, conversation_manager
from api.schemas import ChatTurn
import uuid


def test_conversation_manager():
    """Test the conversation manager functionality."""
    
    print("=" * 80)
    print("Testing Conversation Manager")
    print("=" * 80)
    print()
    
    # Create a new manager instance for testing
    manager = ConversationManager(max_age_hours=24)
    
    # Test 1: New conversation - should be empty
    print("Test 1: New conversation (should be empty)")
    print("-" * 80)
    conv_id1 = str(uuid.uuid4())
    history1 = manager.get_history(conv_id1)
    print(f"Conversation ID: {conv_id1}")
    print(f"Initial history length: {len(history1)}")
    assert len(history1) == 0, "New conversation should be empty"
    print("[OK] New conversation is empty as expected")
    print()
    
    # Test 2: Add a turn
    print("Test 2: Add conversation turn")
    print("-" * 80)
    manager.add_turn(
        conversation_id=conv_id1,
        user_message="What are healthy dinner recipes?",
        assistant_message="Here are some healthy dinner recipes: Grilled salmon with vegetables, Quinoa salad...",
        user_id="test_user_001"
    )
    history2 = manager.get_history(conv_id1)
    print(f"History after adding 1 turn: {len(history2)} turns")
    assert len(history2) == 1, "Should have 1 turn"
    assert history2[0].user == "What are healthy dinner recipes?", "User message should match"
    print(f"  Turn 1 - User: {history2[0].user}")
    print(f"  Turn 1 - Bot: {history2[0].assistant[:50]}...")
    print("[OK] Turn added successfully")
    print()
    
    # Test 3: Add another turn
    print("Test 3: Add second turn (conversation continues)")
    print("-" * 80)
    manager.add_turn(
        conversation_id=conv_id1,
        user_message="Can you tell me more about the first one?",
        assistant_message="Grilled salmon with vegetables is a great choice. Here's how to prepare it...",
        user_id="test_user_001"
    )
    history3 = manager.get_history(conv_id1)
    print(f"History after adding 2 turns: {len(history3)} turns")
    assert len(history3) == 2, "Should have 2 turns"
    print(f"  Turn 1 - User: {history3[0].user}")
    print(f"  Turn 2 - User: {history3[1].user}")
    print("[OK] Second turn added successfully")
    print()
    
    # Test 4: Verify conversation order
    print("Test 4: Verify conversation order")
    print("-" * 80)
    assert history3[0].user == "What are healthy dinner recipes?", "First turn should be first"
    assert history3[1].user == "Can you tell me more about the first one?", "Second turn should be second"
    print("[OK] Conversation order is correct")
    print()
    
    # Test 5: Multiple conversations
    print("Test 5: Multiple independent conversations")
    print("-" * 80)
    conv_id2 = str(uuid.uuid4())
    manager.add_turn(
        conversation_id=conv_id2,
        user_message="What are breakfast ideas?",
        assistant_message="Here are some breakfast ideas: Oatmeal, Scrambled eggs...",
        user_id="test_user_002"
    )
    
    history_conv1 = manager.get_history(conv_id1)
    history_conv2 = manager.get_history(conv_id2)
    
    print(f"Conversation 1 ({conv_id1[:8]}...): {len(history_conv1)} turns")
    print(f"Conversation 2 ({conv_id2[:8]}...): {len(history_conv2)} turns")
    assert len(history_conv1) == 2, "Conversation 1 should have 2 turns"
    assert len(history_conv2) == 1, "Conversation 2 should have 1 turn"
    print("[OK] Conversations are independent")
    print()
    
    # Test 6: Clear conversation
    print("Test 6: Clear a conversation")
    print("-" * 80)
    cleared = manager.clear_conversation(conv_id1)
    assert cleared == True, "Should successfully clear conversation"
    history_after_clear = manager.get_history(conv_id1)
    assert len(history_after_clear) == 0, "Cleared conversation should be empty"
    print(f"Conversation 1 after clear: {len(history_after_clear)} turns")
    print(f"Conversation 2 still exists: {len(manager.get_history(conv_id2))} turns")
    print("[OK] Conversation cleared successfully")
    print()
    
    # Test 7: Test global conversation manager
    print("Test 7: Test global conversation_manager instance")
    print("-" * 80)
    global_conv_id = str(uuid.uuid4())
    conversation_manager.add_turn(
        conversation_id=global_conv_id,
        user_message="Test message",
        assistant_message="Test response",
        user_id="test_user_003"
    )
    global_history = conversation_manager.get_history(global_conv_id)
    assert len(global_history) == 1, "Global manager should work"
    print(f"Global conversation manager: {len(global_history)} turn")
    print("[OK] Global conversation manager works")
    print()
    
    print("=" * 80)
    print("[OK] All conversation manager tests passed!")
    print("=" * 80)
    
    return True


def simulate_conversation_flow():
    """Simulate a realistic conversation flow."""
    
    print("\n" + "=" * 80)
    print("Simulating Realistic Conversation Flow")
    print("=" * 80)
    print()
    
    manager = ConversationManager()
    conv_id = str(uuid.uuid4())
    user_id = "demo_user"
    
    print(f"Conversation ID: {conv_id}")
    print(f"User ID: {user_id}")
    print()
    
    # Simulate a 4-turn conversation
    conversation_turns = [
        {
            "user": "What are some healthy dinner recipes?",
            "assistant": "Here are some healthy dinner options: 1) Grilled salmon with roasted vegetables - high in protein and omega-3s. 2) Quinoa bowl with chickpeas and vegetables - vegetarian and protein-rich. 3) Chicken stir-fry with brown rice - balanced macros."
        },
        {
            "user": "Can you tell me more about the grilled salmon?",
            "assistant": "Grilled salmon is an excellent choice! It's rich in omega-3 fatty acids and protein. For a complete meal, pair it with roasted vegetables like broccoli, bell peppers, and zucchini. Season with herbs like dill or lemon. Cook the salmon for about 6-8 minutes per side on medium heat."
        },
        {
            "user": "What ingredients do I need?",
            "assistant": "For grilled salmon with vegetables, you'll need: Salmon fillets (6-8 oz per person), Fresh vegetables (broccoli, bell peppers, zucchini), Olive oil, Salt and pepper, Fresh herbs (dill or lemon), Optional: garlic, lemon juice for seasoning."
        },
        {
            "user": "How long does it take to cook?",
            "assistant": "The total cooking time is about 20-25 minutes: Prep vegetables (5 min), Season and prepare salmon (5 min), Grill salmon (12-16 min total, 6-8 min per side), Roast vegetables (15-20 min in oven at 400°F). You can prepare vegetables while salmon grills to save time!"
        }
    ]
    
    for i, turn in enumerate(conversation_turns, 1):
        print(f"Turn {i}:")
        print(f"  User: {turn['user']}")
        
        # Get current history
        current_history = manager.get_history(conv_id)
        print(f"  History before this turn: {len(current_history)} previous turns")
        
        # Add the turn
        manager.add_turn(
            conversation_id=conv_id,
            user_message=turn['user'],
            assistant_message=turn['assistant'],
            user_id=user_id
        )
        
        # Verify history grew
        updated_history = manager.get_history(conv_id)
        print(f"  History after this turn: {len(updated_history)} turns")
        print(f"  Bot: {turn['assistant'][:80]}...")
        print()
    
    # Final verification
    final_history = manager.get_history(conv_id)
    print("-" * 80)
    print("Final Conversation Summary:")
    print(f"Total turns: {len(final_history)}")
    print("Conversation flow:")
    for i, turn in enumerate(final_history, 1):
        print(f"  {i}. User asked: {turn.user}")
        print(f"     Bot replied about: {turn.assistant[:60]}...")
    
    print()
    print("=" * 80)
    print("[OK] Conversation flow simulation completed successfully!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        # Run unit tests
        success1 = test_conversation_manager()
        
        # Run simulation
        success2 = simulate_conversation_flow()
        
        if success1 and success2:
            print("\n[OK] All tests passed! Conversation memory is working correctly.")
            sys.exit(0)
        else:
            print("\n[ERROR] Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

