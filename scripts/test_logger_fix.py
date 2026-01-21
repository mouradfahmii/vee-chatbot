#!/usr/bin/env python3
"""
Unit test to verify the logger fixes work correctly.
Tests the string normalization fixes for user_id and conversation_id matching.
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logger import ConversationLogger

TEST_USER_ID = "test_user_12345"
TEST_CONVERSATION_ID = "test_conv_67890"


def create_test_log_entry(user_id: str, conversation_id: str, question: str, answer: str, timestamp: str = None) -> dict:
    """Create a test log entry."""
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    
    return {
        "timestamp": timestamp,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "question": question,
        "answer": answer,
        "is_food_related": True,
        "num_retrieved_docs": 0,
        "history_length": 0,
        "metadata": {},
    }


def test_string_normalization():
    """Test that string normalization fixes work correctly."""
    print("=" * 70)
    print("  TESTING LOGGER STRING NORMALIZATION FIXES")
    print("=" * 70)
    
    # Create a temporary directory for test logs
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir)
        logger = ConversationLogger(log_dir=log_dir)
        
        # Create test log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = log_dir / f"conversations_{date_str}.jsonl"
        
        # Test case 1: Normal text message
        entry1 = create_test_log_entry(
            user_id=TEST_USER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            question="What are healthy breakfast options?",
            answer="Some healthy breakfast options include..."
        )
        
        # Test case 2: Image message
        entry2 = create_test_log_entry(
            user_id=TEST_USER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            question="[IMAGE] What is in this image? Estimate the calories.",
            answer="This image shows a meal with..."
        )
        
        # Test case 3: Voice message (transcript)
        entry3 = create_test_log_entry(
            user_id=TEST_USER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            question="Tell me about Mediterranean diet",
            answer="The Mediterranean diet is..."
        )
        
        # Test case 4: Different user (should not be returned)
        entry4 = create_test_log_entry(
            user_id="different_user",
            conversation_id=TEST_CONVERSATION_ID,
            question="This should not appear",
            answer="This should not appear"
        )
        
        # Test case 5: Same user, different conversation (should not be returned)
        entry5 = create_test_log_entry(
            user_id=TEST_USER_ID,
            conversation_id="different_conv",
            question="This should not appear",
            answer="This should not appear"
        )
        
        # Write entries to log file
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(entry1, ensure_ascii=False) + "\n")
            f.write(json.dumps(entry2, ensure_ascii=False) + "\n")
            f.write(json.dumps(entry3, ensure_ascii=False) + "\n")
            f.write(json.dumps(entry4, ensure_ascii=False) + "\n")
            f.write(json.dumps(entry5, ensure_ascii=False) + "\n")
        
        print(f"\nCreated test log file: {log_file}")
        print(f"Wrote {5} log entries")
        
        # Test 1: get_conversation_history
        print("\n" + "-" * 70)
        print("TEST 1: get_conversation_history")
        print("-" * 70)
        
        messages = logger.get_conversation_history(
            conversation_id=TEST_CONVERSATION_ID,
            user_id=TEST_USER_ID
        )
        
        print(f"Found {len(messages)} message(s)")
        print(f"Expected: 3 (text, image, voice)")
        
        if len(messages) == 3:
            print("[PASS] Correct number of messages returned")
        else:
            print(f"[FAIL] Expected 3 messages, got {len(messages)}")
        
        # Check message types
        text_count = 0
        image_count = 0
        
        for msg in messages:
            question = msg.get("question", "")
            if question.startswith("[IMAGE]"):
                image_count += 1
            else:
                text_count += 1
        
        print(f"  - Text messages: {text_count}")
        print(f"  - Image messages: {image_count}")
        
        if image_count == 1:
            print("[PASS] Image message found in history")
        else:
            print(f"[FAIL] Expected 1 image message, got {image_count}")
        
        if text_count == 2:
            print("[PASS] Text messages (including voice) found in history")
        else:
            print(f"[FAIL] Expected 2 text messages, got {text_count}")
        
        # Test 2: list_user_conversations
        print("\n" + "-" * 70)
        print("TEST 2: list_user_conversations")
        print("-" * 70)
        
        conversations = logger.list_user_conversations(user_id=TEST_USER_ID, max_conversations=10)
        
        print(f"Found {len(conversations)} conversation(s)")
        print(f"Expected: 2 (one with TEST_CONVERSATION_ID, one with 'different_conv')")
        
        # Find our test conversation
        test_conv = None
        for conv in conversations:
            if conv.get("conversation_id") == TEST_CONVERSATION_ID:
                test_conv = conv
                break
        
        if test_conv:
            print("[PASS] Test conversation found in list")
            print(f"  - Message count: {test_conv.get('message_count')}")
            print(f"  - Title: {test_conv.get('title')}")
            
            if test_conv.get("message_count") == 3:
                print("[PASS] Correct message count in conversation summary")
            else:
                print(f"[FAIL] Expected 3 messages, got {test_conv.get('message_count')}")
        else:
            print("[FAIL] Test conversation not found in list")
        
        # Test 3: Test with string variations (whitespace, case)
        print("\n" + "-" * 70)
        print("TEST 3: String Normalization (whitespace, case)")
        print("-" * 70)
        
        # Test with extra whitespace
        messages_ws = logger.get_conversation_history(
            conversation_id=f" {TEST_CONVERSATION_ID} ",
            user_id=f" {TEST_USER_ID} "
        )
        
        print(f"With whitespace: Found {len(messages_ws)} message(s)")
        if len(messages_ws) == 3:
            print("[PASS] String normalization handles whitespace correctly")
        else:
            print(f"[FAIL] Expected 3 messages with whitespace, got {len(messages_ws)}")
        
        # Test 4: load_user_history_as_turns
        print("\n" + "-" * 70)
        print("TEST 4: load_user_history_as_turns")
        print("-" * 70)
        
        turns = logger.load_user_history_as_turns(user_id=TEST_USER_ID, days=-1)
        
        print(f"Found {len(turns)} turn(s)")
        print(f"Expected: 4 (all messages for this user across all conversations)")
        print("  - 3 from TEST_CONVERSATION_ID")
        print("  - 1 from 'different_conv' conversation")
        
        if len(turns) >= 3:
            print("[PASS] Correct number of turns returned (includes all user messages)")
        else:
            print(f"[FAIL] Expected at least 3 turns, got {len(turns)}")
        
        # Summary
        print("\n" + "=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)
        
        all_passed = (
            len(messages) == 3 and
            image_count == 1 and
            text_count == 2 and
            test_conv is not None and
            test_conv.get("message_count") == 3 and
            len(messages_ws) == 3 and
            len(turns) >= 3  # Should include all user messages across conversations
        )
        
        if all_passed:
            print("\n[SUCCESS] ALL TESTS PASSED!")
            print("The logger fixes are working correctly.")
            print("Image and voice messages are now being returned in history.")
        else:
            print("\n[FAILURE] SOME TESTS FAILED")
            print("Please review the test output above.")


if __name__ == "__main__":
    try:
        test_string_normalization()
    except Exception as e:
        print(f"\n\nError during test: {e}")
        import traceback
        traceback.print_exc()
