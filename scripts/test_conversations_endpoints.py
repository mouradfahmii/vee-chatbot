"""
Test script for conversation list and detail endpoints.
Simulates both GET /conversations and GET /conversations/{conversation_id} endpoints.
"""

import json
import sys
from pathlib import Path

# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python < 3.7 doesn't have reconfigure
        pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logger import conversation_logger


def test_list_conversations(user_id: str):
    """Test listing all conversations for a user."""
    print("=" * 80)
    print(f"TEST 1: List Conversations for user_id='{user_id}'")
    print("=" * 80)
    print()
    
    try:
        conversations = conversation_logger.list_user_conversations(
            user_id=user_id,
            max_conversations=100
        )
        
        print(f"Found {len(conversations)} conversations")
        print()
        
        if not conversations:
            print("No conversations found for this user.")
            return None
        
        # Display first few conversations
        print("Conversation Summaries (sorted by most recent first):")
        print("-" * 80)
        
        for i, conv in enumerate(conversations[:5], 1):  # Show first 5
            print(f"\n{i}. Conversation ID: {conv['conversation_id']}")
            print(f"   Title: {conv['title']}")
            print(f"   Preview: {conv['preview']}")
            print(f"   Messages: {conv['message_count']}")
            print(f"   Created: {conv['created_at']}")
            print(f"   Last Updated: {conv['last_updated']}")
        
        if len(conversations) > 5:
            print(f"\n... and {len(conversations) - 5} more conversations")
        
        print()
        print("=" * 80)
        print()
        
        # Return first conversation_id for testing detail endpoint
        return conversations[0]['conversation_id'] if conversations else None
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_conversation_history(conversation_id: str, user_id: str):
    """Test getting full conversation history."""
    print("=" * 80)
    print(f"TEST 2: Get Conversation History")
    print(f"  conversation_id='{conversation_id}'")
    print(f"  user_id='{user_id}'")
    print("=" * 80)
    print()
    
    try:
        messages = conversation_logger.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not messages:
            print("No messages found for this conversation.")
            print("(This could mean the conversation doesn't exist or belongs to a different user)")
            return
        
        print(f"Found {len(messages)} messages in this conversation")
        print()
        print("Full Conversation History (chronological order):")
        print("-" * 80)
        
        for i, msg in enumerate(messages, 1):
            print(f"\n--- Message {i} ({msg['timestamp']}) ---")
            print(f"User: {msg['question']}")
            print(f"Assistant: {msg['answer'][:200]}...")  # Truncate long answers
            if len(msg['answer']) > 200:
                print(f"        (answer truncated, full length: {len(msg['answer'])} chars)")
        
        print()
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def test_security_check():
    """Test that users cannot access other users' conversations."""
    print("=" * 80)
    print("TEST 3: Security Check - User Access Control")
    print("=" * 80)
    print()
    
    # Try to access a conversation with wrong user_id
    test_conversation_id = "conv-breakfast-001"
    wrong_user_id = "wrong_user_999"
    
    print(f"Attempting to access conversation '{test_conversation_id}'")
    print(f"with user_id '{wrong_user_id}' (should return empty/404)")
    print()
    
    messages = conversation_logger.get_conversation_history(
        conversation_id=test_conversation_id,
        user_id=wrong_user_id
    )
    
    if not messages:
        print("[PASS] Security check passed: No access granted to wrong user")
    else:
        print("[FAIL] Security check failed: Wrong user was able to access conversation!")
    
    print()
    print("=" * 80)
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CONVERSATION ENDPOINTS SIMULATION")
    print("=" * 80)
    print()
    
    # Test with existing user from logs
    test_user_ids = [
        "demo_user_001",
        "test_user_voice_001",
        "test_user_voice_002",
    ]
    
    for user_id in test_user_ids:
        print(f"\n{'='*80}")
        print(f"Testing with user_id: {user_id}")
        print(f"{'='*80}\n")
        
        # Test 1: List conversations
        conversation_id = test_list_conversations(user_id)
        
        # Test 2: Get conversation history (if we found a conversation)
        if conversation_id:
            test_get_conversation_history(conversation_id, user_id)
        else:
            print(f"No conversations found for {user_id}, skipping detail test")
            print()
        
        # Test 3: Security check (only once)
        if user_id == test_user_ids[0]:
            test_security_check()
    
    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("- Test 1: List conversations endpoint simulation")
    print("- Test 2: Get conversation history endpoint simulation")
    print("- Test 3: Security check (user access control)")
    print()
    print("To test via HTTP API, ensure the server is running and use:")
    print("  GET /conversations?user_id=<user_id>")
    print("  GET /conversations/<conversation_id>?user_id=<user_id>")


if __name__ == "__main__":
    main()

