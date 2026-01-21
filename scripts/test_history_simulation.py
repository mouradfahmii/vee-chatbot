#!/usr/bin/env python3
"""
Simulation script to test chat, image, and voice messages,
then verify they appear in conversation history.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from app.logger import conversation_logger

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY") or os.getenv("VEE_CHATBOT_API_KEY", "dev")
TEST_USER_ID = "test_user_12345"
TEST_IMAGE_PATH = Path(__file__).parent.parent / "test_images" / "test_meal.jpg"


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_chat_message(base_url: str, api_key: str, user_id: str) -> tuple[str, str]:
    """Test sending a chat message."""
    print_section("TEST 1: Sending Chat Message")
    
    url = f"{base_url}/chat"
    headers = {"X-API-Key": api_key}
    payload = {
        "message": "What are some healthy breakfast options?",
        "user_id": user_id,
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        conversation_id = data.get("conversation_id")
        answer = data.get("answer", "")
        print(f"✓ Chat message sent successfully")
        print(f"Conversation ID: {conversation_id}")
        print(f"Answer preview: {answer[:100]}...")
        return conversation_id, answer
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None, None


def test_image_message(base_url: str, api_key: str, user_id: str, conversation_id: str, image_path: Path) -> tuple[str, str]:
    """Test sending an image message."""
    print_section("TEST 2: Sending Image Message")
    
    if not image_path.exists():
        print(f"✗ Image file not found: {image_path}")
        print("Skipping image test...")
        return conversation_id, None
    
    url = f"{base_url}/chat/image"
    headers = {"X-API-Key": api_key}
    
    with open(image_path, "rb") as f:
        files = {"image": (image_path.name, f, "image/jpeg")}
        data = {
            "question": "What is in this image? Estimate the calories.",
            "user_id": user_id,
            "conversation_id": conversation_id,
        }
        
        print(f"URL: {url}")
        print(f"Image: {image_path}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, files=files, data=data, headers=headers, timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            conv_id = response_data.get("conversation_id", conversation_id)
            answer = response_data.get("answer", "")
            print(f"✓ Image message sent successfully")
            print(f"Conversation ID: {conv_id}")
            print(f"Answer preview: {answer[:100]}...")
            return conv_id, answer
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return conversation_id, None


def test_voice_message(base_url: str, api_key: str, user_id: str, conversation_id: str) -> tuple[str, str]:
    """Test sending a voice message (simulated with a text endpoint)."""
    print_section("TEST 3: Sending Voice Message")
    
    # For testing, we'll use the voice/text endpoint which accepts audio
    # Since we don't have a real audio file, we'll skip this or create a mock
    # In a real scenario, you would send an actual audio file
    
    print("Note: Voice message test requires an actual audio file.")
    print("Skipping voice test for now (would need WebM/MP3 file).")
    print("To test voice messages, use:")
    print(f"  curl -X POST '{base_url}/chat/voice/text' \\")
    print(f"    -H 'X-API-Key: {api_key}' \\")
    print(f"    -F 'audio=@audio_file.webm' \\")
    print(f"    -F 'user_id={user_id}' \\")
    print(f"    -F 'conversation_id={conversation_id}'")
    
    return conversation_id, None


def test_list_conversations(base_url: str, api_key: str, user_id: str) -> list:
    """Test listing all conversations for a user."""
    print_section("TEST 4: Listing All Conversations")
    
    url = f"{base_url}/conversations"
    headers = {"X-API-Key": api_key}
    params = {"user_id": user_id}
    
    print(f"URL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        conversations = data.get("conversations", [])
        total = data.get("total", 0)
        print(f"✓ Found {total} conversation(s)")
        
        for i, conv in enumerate(conversations, 1):
            print(f"\n  Conversation {i}:")
            print(f"    ID: {conv.get('conversation_id')}")
            print(f"    Title: {conv.get('title')}")
            print(f"    Preview: {conv.get('preview')}")
            print(f"    Messages: {conv.get('message_count')}")
            print(f"    Created: {conv.get('created_at')}")
            print(f"    Updated: {conv.get('last_updated')}")
        
        return conversations
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return []


def test_get_conversation_history(base_url: str, api_key: str, user_id: str, conversation_id: str) -> list:
    """Test getting full conversation history."""
    print_section("TEST 5: Getting Conversation History")
    
    url = f"{base_url}/conversations/{conversation_id}"
    headers = {"X-API-Key": api_key}
    params = {"user_id": user_id}
    
    print(f"URL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        message_count = data.get("message_count", 0)
        print(f"✓ Found {message_count} message(s) in conversation")
        
        print("\n  Messages:")
        for i, msg in enumerate(messages, 1):
            question = msg.get("question", "")
            answer = msg.get("answer", "")
            timestamp = msg.get("timestamp", "")
            
            # Check message type
            msg_type = "TEXT"
            if question.startswith("[IMAGE]"):
                msg_type = "IMAGE"
            elif len(question) > 0 and not question.startswith("["):
                msg_type = "VOICE/TEXT"
            
            print(f"\n    Message {i} ({msg_type}):")
            print(f"      Question: {question[:80]}...")
            print(f"      Answer: {answer[:80]}...")
            print(f"      Timestamp: {timestamp}")
        
        return messages
    elif response.status_code == 404:
        print(f"✗ Conversation not found (404)")
        print("This might mean the conversation_id doesn't match or user_id doesn't match")
        return []
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return []


def test_direct_logger_access(user_id: str, conversation_id: str) -> None:
    """Test accessing logs directly via logger."""
    print_section("TEST 6: Direct Logger Access")
    
    print(f"User ID: {user_id}")
    print(f"Conversation ID: {conversation_id}")
    
    # Test get_conversation_history
    print("\n  Testing get_conversation_history...")
    messages = conversation_logger.get_conversation_history(
        conversation_id=conversation_id,
        user_id=user_id
    )
    print(f"  Found {len(messages)} message(s) via logger")
    
    for i, msg in enumerate(messages, 1):
        question = msg.get("question", "")
        msg_type = "TEXT"
        if question.startswith("[IMAGE]"):
            msg_type = "IMAGE"
        print(f"    {i}. [{msg_type}] {question[:60]}...")
    
    # Test list_user_conversations
    print("\n  Testing list_user_conversations...")
    conversations = conversation_logger.list_user_conversations(user_id=user_id, max_conversations=10)
    print(f"  Found {len(conversations)} conversation(s) via logger")
    
    for i, conv in enumerate(conversations, 1):
        print(f"    {i}. {conv.get('conversation_id')} - {conv.get('title')[:50]}...")


def main() -> None:
    """Run the simulation tests."""
    print("\n" + "=" * 70)
    print("  HISTORY RETRIEVAL SIMULATION TEST")
    print("=" * 70)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"User ID: {TEST_USER_ID}")
    print(f"Image Path: {TEST_IMAGE_PATH}")
    
    # Wait a moment for any previous requests to complete
    print("\nWaiting 2 seconds for any previous requests to complete...")
    time.sleep(2)
    
    # Test 1: Send chat message
    conversation_id, _ = test_chat_message(API_BASE_URL, API_KEY, TEST_USER_ID)
    if not conversation_id:
        print("\n✗ Failed to send chat message. Cannot continue.")
        return
    
    time.sleep(1)  # Small delay between requests
    
    # Test 2: Send image message
    conversation_id, _ = test_image_message(
        API_BASE_URL, API_KEY, TEST_USER_ID, conversation_id, TEST_IMAGE_PATH
    )
    
    time.sleep(1)  # Small delay between requests
    
    # Test 3: Send another chat message to verify mixed types
    print_section("TEST 3: Sending Another Chat Message")
    conversation_id, _ = test_chat_message(API_BASE_URL, API_KEY, TEST_USER_ID)
    if conversation_id:
        time.sleep(1)
    
    # Test 4: List all conversations
    conversations = test_list_conversations(API_BASE_URL, API_KEY, TEST_USER_ID)
    
    # Test 5: Get conversation history
    if conversation_id:
        messages = test_get_conversation_history(
            API_BASE_URL, API_KEY, TEST_USER_ID, conversation_id
        )
        
        # Verify message types
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
    
    # Test 6: Direct logger access
    if conversation_id:
        test_direct_logger_access(TEST_USER_ID, conversation_id)
    
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
        print(f"\n\n✗ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
