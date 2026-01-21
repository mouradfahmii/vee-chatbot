#!/usr/bin/env python3
"""
Direct simulation test that doesn't require the API server.
Tests chat, image, and voice messages by calling the chatbot directly,
then verifies they appear in conversation history.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.chatbot import bot
from app.logger import conversation_logger
from app.conversation_manager import conversation_manager
import uuid

TEST_USER_ID = "test_user_direct_12345"


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_chat_message(user_id: str, conversation_id: str = None) -> tuple[str, str]:
    """Test sending a chat message directly."""
    print_section("TEST 1: Sending Chat Message (Direct)")
    
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    
    question = "What are some healthy breakfast options?"
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Question: {question}")
    
    # Get history from conversation manager
    history_turns = conversation_manager.get_history(conversation_id)
    history = [{"user": turn.user, "assistant": turn.assistant} for turn in history_turns]
    
    # Get answer from bot
    answer = bot.answer(
        question=question,
        history=history if history else None,
        user_id=user_id,
        conversation_id=conversation_id
    )
    
    # Store in conversation manager
    conversation_manager.add_turn(
        conversation_id=conversation_id,
        user_message=question,
        assistant_message=answer,
        user_id=user_id,
    )
    
    print(f"Answer: {answer[:100]}...")
    print("✓ Chat message processed successfully")
    
    return conversation_id, answer


def test_image_message(user_id: str, conversation_id: str, image_path: Path) -> tuple[str, str]:
    """Test sending an image message directly."""
    print_section("TEST 2: Sending Image Message (Direct)")
    
    if not image_path.exists():
        print(f"✗ Image file not found: {image_path}")
        return conversation_id, None
    
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Image: {image_path}")
    
    # Read image data
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Get history from conversation manager
    history_turns = conversation_manager.get_history(conversation_id)
    history = [{"user": turn.user, "assistant": turn.assistant} for turn in history_turns]
    
    question = "What is in this image? Estimate the calories."
    
    # Get answer from bot
    answer = bot.answer_with_image(
        image_data=image_data,
        question=question,
        history=history if history else None,
        user_id=user_id,
        conversation_id=conversation_id
    )
    
    # Store in conversation manager
    conversation_manager.add_turn(
        conversation_id=conversation_id,
        user_message=f"[IMAGE] {question}",
        assistant_message=answer,
        user_id=user_id,
    )
    
    print(f"Answer: {answer[:100]}...")
    print("✓ Image message processed successfully")
    
    return conversation_id, answer


def test_voice_message(user_id: str, conversation_id: str) -> tuple[str, str]:
    """Test sending a voice message (simulated as text)."""
    print_section("TEST 3: Sending Voice Message (Simulated)")
    
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    
    # Simulate voice message - in real scenario this would be transcribed audio
    transcript = "Tell me about Mediterranean diet benefits"
    print(f"Transcript: {transcript}")
    
    # Get history from conversation manager
    history_turns = conversation_manager.get_history(conversation_id)
    history = [{"user": turn.user, "assistant": turn.assistant} for turn in history_turns]
    
    # Get answer from bot (voice messages are processed as text after transcription)
    answer = bot.answer(
        question=transcript,
        history=history if history else None,
        user_id=user_id,
        conversation_id=conversation_id
    )
    
    # Store in conversation manager
    conversation_manager.add_turn(
        conversation_id=conversation_id,
        user_message=transcript,
        assistant_message=answer,
        user_id=user_id,
    )
    
    print(f"Answer: {answer[:100]}...")
    print("✓ Voice message processed successfully")
    
    return conversation_id, answer


def test_list_conversations(user_id: str) -> list:
    """Test listing all conversations for a user."""
    print_section("TEST 4: Listing All Conversations (Direct Logger)")
    
    print(f"User ID: {user_id}")
    
    conversations = conversation_logger.list_user_conversations(user_id=user_id, max_conversations=10)
    
    print(f"Found {len(conversations)} conversation(s)")
    
    for i, conv in enumerate(conversations, 1):
        print(f"\n  Conversation {i}:")
        print(f"    ID: {conv.get('conversation_id')}")
        print(f"    Title: {conv.get('title')}")
        print(f"    Preview: {conv.get('preview')}")
        print(f"    Messages: {conv.get('message_count')}")
        print(f"    Created: {conv.get('created_at')}")
        print(f"    Updated: {conv.get('last_updated')}")
    
    return conversations


def test_get_conversation_history(user_id: str, conversation_id: str) -> list:
    """Test getting full conversation history."""
    print_section("TEST 5: Getting Conversation History (Direct Logger)")
    
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    
    messages = conversation_logger.get_conversation_history(
        conversation_id=conversation_id,
        user_id=user_id
    )
    
    print(f"Found {len(messages)} message(s) in conversation")
    
    print("\n  Messages:")
    for i, msg in enumerate(messages, 1):
        question = msg.get("question", "")
        answer = msg.get("answer", "")
        timestamp = msg.get("timestamp", "")
        
        # Check message type
        msg_type = "TEXT"
        if question.startswith("[IMAGE]"):
            msg_type = "IMAGE"
        
        print(f"\n    Message {i} ({msg_type}):")
        print(f"      Question: {question[:80]}...")
        print(f"      Answer: {answer[:80]}...")
        print(f"      Timestamp: {timestamp}")
    
    return messages


def main() -> None:
    """Run the direct simulation tests."""
    print("\n" + "=" * 70)
    print("  DIRECT HISTORY RETRIEVAL SIMULATION TEST")
    print("=" * 70)
    print(f"\nUser ID: {TEST_USER_ID}")
    
    image_path = Path(__file__).parent.parent / "test_images" / "test_meal.jpg"
    print(f"Image Path: {image_path}")
    
    # Test 1: Send chat message
    conversation_id, _ = test_chat_message(TEST_USER_ID)
    
    # Wait a moment for logging to complete
    import time
    time.sleep(1)
    
    # Test 2: Send image message
    conversation_id, _ = test_image_message(TEST_USER_ID, conversation_id, image_path)
    time.sleep(1)
    
    # Test 3: Send voice message (simulated)
    conversation_id, _ = test_voice_message(TEST_USER_ID, conversation_id)
    time.sleep(1)
    
    # Test 4: Send another chat message
    conversation_id, _ = test_chat_message(TEST_USER_ID, conversation_id)
    time.sleep(2)  # Wait for all logging to complete
    
    # Test 5: List all conversations
    conversations = test_list_conversations(TEST_USER_ID)
    
    # Test 6: Get conversation history
    if conversation_id:
        messages = test_get_conversation_history(TEST_USER_ID, conversation_id)
        
        # Verification
        print_section("VERIFICATION: Message Types Found")
        text_count = 0
        image_count = 0
        
        for msg in messages:
            question = msg.get("question", "")
            if question.startswith("[IMAGE]"):
                image_count += 1
            else:
                text_count += 1
        
        print(f"Text messages: {text_count}")
        print(f"Image messages: {image_count}")
        print(f"Total messages: {len(messages)}")
        
        if image_count > 0:
            print("\n✓ SUCCESS: Image messages are being returned in history!")
        else:
            print("\n✗ WARNING: No image messages found in history")
        
        if text_count >= 2:
            print("✓ SUCCESS: Text messages (including voice transcripts) are being returned!")
        else:
            print("✗ WARNING: Expected more text messages")
    
    print_section("SIMULATION COMPLETE")
    print("\nSummary:")
    print(f"  - User ID used: {TEST_USER_ID}")
    print(f"  - Conversation ID: {conversation_id}")
    print(f"  - Total conversations found: {len(conversations)}")
    if conversation_id:
        print(f"  - Messages in conversation: {len(messages) if 'messages' in locals() else 0}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nError during simulation: {e}")
        import traceback
        traceback.print_exc()
