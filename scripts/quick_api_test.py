#!/usr/bin/env python3
"""
Quick API test script - Simple examples for testing endpoints
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "http://127.0.0.1:8001"
API_KEY = os.getenv("API_KEY") or os.getenv("VEE_CHATBOT_API_KEY")
USER_ID = "test_user_123"

headers = {}
if API_KEY:
    headers["X-API-Key"] = API_KEY

def test_text_chat():
    """Test text chat."""
    print("📝 Testing Text Chat...")
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={
            "message": "What are healthy breakfast options?",
            "user_id": USER_ID
        },
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Conversation ID: {data.get('conversation_id')}")
        print(f"✓ Answer: {data.get('answer', '')[:150]}...")
        return data.get('conversation_id')
    else:
        print(f"✗ Error: {response.json().get('detail', 'Unknown error')}")
    return None

def test_image_chat(conversation_id=None):
    """Test image chat."""
    print("\n🖼️  Testing Image Chat...")
    
    # Find any test image
    test_images_dir = Path(__file__).parent.parent / "test_images"
    image_path = None
    for img in ["scaled_34.jpg", "test_meal.jpg", "non_food_test.jpg"]:
        if (test_images_dir / img).exists():
            image_path = test_images_dir / img
            break
    
    if not image_path:
        print("✗ No test images found")
        return conversation_id
    
    with open(image_path, "rb") as f:
        files = {"image": (image_path.name, f, "image/jpeg")}
        data = {
            "question": "What is in this image? Estimate calories.",
            "user_id": USER_ID
        }
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        response = requests.post(
            f"{API_BASE_URL}/chat/image",
            files=files,
            data=data,
            headers=headers
        )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Conversation ID: {data.get('conversation_id')}")
        print(f"✓ Answer: {data.get('answer', '')[:150]}...")
        return data.get('conversation_id')
    else:
        print(f"✗ Error: {response.json().get('detail', 'Unknown error')}")
    return conversation_id

def test_list_conversations():
    """Test listing conversations."""
    print("\n📋 Testing Conversation History (List)...")
    response = requests.get(
        f"{API_BASE_URL}/conversations",
        params={"user_id": USER_ID},
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total conversations: {data.get('total', 0)}")
        for conv in data.get('conversations', [])[:3]:
            print(f"  - {conv.get('conversation_id')}: {conv.get('title', '')[:50]}")
        return data.get('conversations', [{}])[0].get('conversation_id') if data.get('conversations') else None
    return None

def test_get_conversation(conversation_id):
    """Test getting full conversation."""
    if not conversation_id:
        print("\n✗ No conversation ID available")
        return
    
    print(f"\n📖 Testing Get Conversation Details...")
    response = requests.get(
        f"{API_BASE_URL}/conversations/{conversation_id}",
        params={"user_id": USER_ID},
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Messages: {data.get('message_count', 0)}")
        for i, msg in enumerate(data.get('messages', [])[:2], 1):
            print(f"  Message {i}:")
            print(f"    Q: {msg.get('question', '')[:60]}...")
            print(f"    A: {msg.get('answer', '')[:60]}...")

if __name__ == "__main__":
    print("=" * 60)
    print("  QUICK API TEST")
    print("=" * 60)
    
    # Test image chat (works even with ChromaDB issue)
    conv_id = test_image_chat()
    
    # Test conversation history
    conv_id = test_list_conversations() or conv_id
    
    # Get full conversation
    if conv_id:
        test_get_conversation(conv_id)
    
    print("\n" + "=" * 60)
    print("  Test Complete!")
    print(f"  API Docs: {API_BASE_URL}/docs")
    print("=" * 60)
