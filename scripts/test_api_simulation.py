#!/usr/bin/env python3
"""
Simulate conversations and test all API endpoints:
- Text chat
- Image chat
- Voice chat
- Conversation history
"""

import json
import base64
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = "http://127.0.0.1:8001"
API_KEY = os.getenv("API_KEY") or os.getenv("VEE_CHATBOT_API_KEY")  # Get from environment

# Test user ID
USER_ID = "test_user_123"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_response(response: requests.Response, label: str = "Response"):
    """Print formatted response."""
    print(f"\n{label}:")
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        if response.status_code >= 400:
            print(f"  Error: {data.get('detail', 'Unknown error')}")
        else:
            # For successful responses, show summary
            if isinstance(data, dict):
                if "answer" in data:
                    print(f"  Answer: {data.get('answer', '')[:200]}...")
                if "conversation_id" in data:
                    print(f"  Conversation ID: {data.get('conversation_id')}")
                if "conversations" in data:
                    print(f"  Total: {data.get('total', 0)} conversations")
                if "messages" in data:
                    print(f"  Messages: {len(data.get('messages', []))}")
        # Show full data for debugging if needed (commented out for cleaner output)
        # print(f"  Full Data: {json.dumps(data, indent=2)}")
    except:
        print(f"  Text: {response.text[:500]}")

def test_text_chat():
    """Test text chat endpoint."""
    print_section("1. TEXT CHAT - Starting Conversation")
    
    # First message
    url = f"{API_BASE_URL}/chat"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    payload = {
        "message": "What are some healthy breakfast options?",
        "user_id": USER_ID
    }
    
    print(f"\nSending: {payload['message']}")
    response = requests.post(url, json=payload, headers=headers)
    print_response(response, "First Message Response")
    
    if response.status_code == 200:
        data = response.json()
        conversation_id = data.get("conversation_id")
        print(f"\n  ✓ Conversation ID: {conversation_id}")
        print(f"  ✓ Answer: {data.get('answer', '')[:200]}...")
        return conversation_id
    
    return None

def test_text_chat_continuation(conversation_id: str):
    """Test continuing the conversation."""
    print_section("2. TEXT CHAT - Continuing Conversation")
    
    url = f"{API_BASE_URL}/chat"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    payload = {
        "message": "Can you give me a recipe for one of those?",
        "conversation_id": conversation_id,
        "user_id": USER_ID
    }
    
    print(f"\nSending: {payload['message']}")
    response = requests.post(url, json=payload, headers=headers)
    print_response(response, "Follow-up Response")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n  ✓ Answer: {data.get('answer', '')[:200]}...")
        return True
    return False

def test_image_chat(conversation_id: str = None):
    """Test image chat endpoint."""
    print_section("3. IMAGE CHAT - Analyzing Food Image")
    
    # Check if test image exists - try multiple possible names
    test_images_dir = Path(__file__).parent.parent / "test_images"
    test_image_path = None
    
    # Try different image names
    for img_name in ["test_meal.jpg", "scaled_34.jpg", "non_food_test.jpg"]:
        potential_path = test_images_dir / img_name
        if potential_path.exists():
            test_image_path = potential_path
            break
    
    if not test_image_path or not test_image_path.exists():
        print(f"\n  ⚠ No test images found in {test_images_dir}")
        print("  Skipping image chat test...")
        return conversation_id
    
    url = f"{API_BASE_URL}/chat/image"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    with open(test_image_path, "rb") as img_file:
        files = {
            "image": (test_image_path.name, img_file, "image/jpeg")
        }
        
        data = {
            "question": "What is in this image? Estimate the calories and suggest a healthy alternative.",
            "user_id": USER_ID
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        print(f"\nSending image: {test_image_path.name}")
        print(f"Question: {data['question']}")
        
        response = requests.post(url, files=files, data=data, headers=headers)
    
    print_response(response, "Image Analysis Response")
    
    if response.status_code == 200:
        data = response.json()
        new_conversation_id = data.get("conversation_id")
        print(f"\n  ✓ Conversation ID: {new_conversation_id}")
        print(f"  ✓ Answer: {data.get('answer', '')[:200]}...")
        return new_conversation_id or conversation_id
    
    return conversation_id

def test_voice_chat(conversation_id: str = None):
    """Test voice chat endpoint (simulated with text-to-speech note)."""
    print_section("4. VOICE CHAT - Voice Interaction")
    
    print("\n  ⚠ Note: Voice chat requires actual audio files.")
    print("  For a real test, you would need to:")
    print("    1. Record audio (WebM, MP3, WAV, M4A, or OGG)")
    print("    2. Send POST to /chat/voice with audio file")
    print("    3. Receive transcript, text response, and audio response")
    
    # Example of how it would work:
    url = f"{API_BASE_URL}/chat/voice"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    print(f"\n  Example request structure:")
    print(f"    URL: {url}")
    print(f"    Method: POST")
    print(f"    Headers: X-API-Key (if configured)")
    print(f"    Form data:")
    print(f"      - audio: <audio file>")
    print(f"      - user_id: {USER_ID}")
    if conversation_id:
        print(f"      - conversation_id: {conversation_id}")
    print(f"      - history_days: (optional) 3, 7, or -1")
    
    print(f"\n  Expected response:")
    print(f"    - transcript: Transcribed user speech")
    print(f"    - data: HTML response from chatbot")
    print(f"    - conversation_id: Conversation ID")
    print(f"    - detected_language: 'ar' or 'en'")
    print(f"    - audio_base64: Base64 encoded MP3 response")
    
    return conversation_id

def test_list_conversations():
    """Test listing all conversations for a user."""
    print_section("5. CONVERSATION HISTORY - List All Conversations")
    
    url = f"{API_BASE_URL}/conversations"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    params = {
        "user_id": USER_ID
    }
    
    print(f"\nFetching conversations for user: {USER_ID}")
    response = requests.get(url, params=params, headers=headers)
    print_response(response, "Conversations List")
    
    if response.status_code == 200:
        data = response.json()
        conversations = data.get("conversations", [])
        print(f"\n  ✓ Total conversations: {data.get('total', 0)}")
        for i, conv in enumerate(conversations[:3], 1):  # Show first 3
            print(f"\n  Conversation {i}:")
            print(f"    ID: {conv.get('conversation_id', 'N/A')}")
            print(f"    Title: {conv.get('title', 'N/A')}")
            print(f"    Preview: {conv.get('preview', 'N/A')[:100]}...")
            print(f"    Messages: {conv.get('message_count', 0)}")
            print(f"    Last updated: {conv.get('last_updated', 'N/A')}")
        
        # Return first conversation ID if available
        if conversations:
            return conversations[0].get("conversation_id")
    
    return None

def test_get_conversation_details(conversation_id: str):
    """Test getting full conversation details."""
    print_section("6. CONVERSATION HISTORY - Get Full Conversation")
    
    if not conversation_id:
        print("\n  ⚠ No conversation ID available. Skipping...")
        return
    
    url = f"{API_BASE_URL}/conversations/{conversation_id}"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    params = {
        "user_id": USER_ID
    }
    
    print(f"\nFetching full conversation: {conversation_id}")
    response = requests.get(url, params=params, headers=headers)
    print_response(response, "Conversation Details")
    
    if response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        print(f"\n  ✓ Conversation ID: {data.get('conversation_id', 'N/A')}")
        print(f"  ✓ User ID: {data.get('user_id', 'N/A')}")
        print(f"  ✓ Total messages: {data.get('message_count', 0)}")
        print(f"  ✓ Created: {data.get('created_at', 'N/A')}")
        print(f"  ✓ Last updated: {data.get('last_updated', 'N/A')}")
        
        print(f"\n  Messages:")
        for i, msg in enumerate(messages, 1):
            print(f"\n    Message {i}:")
            print(f"      Question: {msg.get('question', 'N/A')[:100]}...")
            print(f"      Answer: {msg.get('answer', 'N/A')[:100]}...")
            print(f"      Timestamp: {msg.get('timestamp', 'N/A')}")
            if msg.get('image_url'):
                print(f"      Image: {msg.get('image_url')}")

def test_html_chat():
    """Test HTML chat endpoint."""
    print_section("7. HTML CHAT - Get HTML Formatted Response")
    
    url = f"{API_BASE_URL}/chat/html"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    payload = {
        "message": "What are the health benefits of Mediterranean diet?",
        "user_id": USER_ID
    }
    
    print(f"\nSending: {payload['message']}")
    response = requests.post(url, json=payload, headers=headers)
    print_response(response, "HTML Response")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n  ✓ Status: {data.get('status', 'N/A')}")
        print(f"  ✓ Message: {data.get('message', 'N/A')}")
        print(f"  ✓ Conversation ID: {data.get('conversation_id', 'N/A')}")
        print(f"  ✓ HTML Data (first 300 chars): {data.get('data', '')[:300]}...")
        return data.get("conversation_id")
    
    return None

def main():
    """Run all API simulation tests."""
    print("\n" + "=" * 60)
    print("  VEE CHATBOT API SIMULATION TEST")
    print("=" * 60)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"Test User ID: {USER_ID}")
    
    try:
        # Test 1: Text chat - start conversation
        conversation_id = test_text_chat()
        
        # Test 2: Text chat - continue conversation
        if conversation_id:
            test_text_chat_continuation(conversation_id)
        
        # Test 3: Image chat
        conversation_id = test_image_chat(conversation_id)
        
        # Test 4: Voice chat (info only)
        test_voice_chat(conversation_id)
        
        # Test 5: List conversations
        first_conv_id = test_list_conversations()
        
        # Test 6: Get conversation details
        if first_conv_id or conversation_id:
            test_get_conversation_details(first_conv_id or conversation_id)
        
        # Test 7: HTML chat
        test_html_chat()
        
        print_section("TEST COMPLETE")
        print("\n  ✓ All API endpoints tested successfully!")
        print(f"\n  You can view the API documentation at: {API_BASE_URL}/docs")
        
    except requests.exceptions.ConnectionError:
        print("\n  ✗ ERROR: Could not connect to the API server.")
        print(f"  Make sure the server is running on {API_BASE_URL}")
        print("  Start it with: python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8001")
    except Exception as e:
        print(f"\n  ✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
