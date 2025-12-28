#!/usr/bin/env python3
"""Test script to verify conversations API endpoints work correctly."""

import sys
import requests
import json
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your server URL
API_KEY = "YOUR_API_KEY"  # Change to your API key
TEST_USER_ID = "test_user_api_001"  # Use a consistent user_id

def test_conversations_api():
    """Test the conversations listing and detail endpoints."""
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print("=" * 70)
    print("Testing Conversations API")
    print("=" * 70)
    
    # Step 1: Make a chat request first to create a conversation
    print(f"\n1. Creating a test conversation...")
    print(f"   User ID: {TEST_USER_ID}")
    
    chat_payload = {
        "message": "What are healthy breakfast options?",
        "user_id": TEST_USER_ID,
        "conversation_id": None  # Let it generate a new one
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            headers=headers,
            json=chat_payload,
            timeout=30
        )
        response.raise_for_status()
        chat_data = response.json()
        conversation_id = chat_data.get("conversation_id")
        print(f"   ✓ Chat successful")
        print(f"   Generated conversation_id: {conversation_id}")
        print(f"   Answer preview: {chat_data.get('answer', '')[:50]}...")
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Chat failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return
    
    # Step 2: Make another chat in the same conversation
    print(f"\n2. Adding another message to the same conversation...")
    chat_payload2 = {
        "message": "Tell me more about oatmeal",
        "user_id": TEST_USER_ID,
        "conversation_id": conversation_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            headers=headers,
            json=chat_payload2,
            timeout=30
        )
        response.raise_for_status()
        print(f"   ✓ Second message successful")
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Second message failed: {e}")
        return
    
    # Step 3: List conversations
    print(f"\n3. Listing conversations for user_id: {TEST_USER_ID}")
    try:
        response = requests.get(
            f"{BASE_URL}/conversations",
            headers=headers,
            params={"user_id": TEST_USER_ID},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print(f"   ✓ List request successful")
        print(f"   Status: {response.status_code}")
        print(f"   Total conversations: {data.get('total', 0)}")
        print(f"   Conversations found: {len(data.get('conversations', []))}")
        
        if data.get('conversations'):
            print(f"\n   Conversations:")
            for i, conv in enumerate(data['conversations'][:5], 1):  # Show first 5
                print(f"     {i}. {conv.get('conversation_id')}")
                print(f"        Title: {conv.get('title', '')[:60]}")
                print(f"        Messages: {conv.get('message_count')}")
                print(f"        Last updated: {conv.get('last_updated')}")
        else:
            print(f"   ⚠️  No conversations found!")
            print(f"   This could mean:")
            print(f"     - The user_id doesn't match what was used in chat requests")
            print(f"     - Logs haven't been written yet (check server logs directory)")
            print(f"     - There's a timezone issue with log file naming")
            return
        
    except requests.exceptions.RequestException as e:
        print(f"   ✗ List request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return
    
    # Step 4: Get conversation detail
    if data.get('conversations'):
        test_conv_id = data['conversations'][0]['conversation_id']
        print(f"\n4. Getting conversation detail for: {test_conv_id}")
        try:
            response = requests.get(
                f"{BASE_URL}/conversations/{test_conv_id}",
                headers=headers,
                params={"user_id": TEST_USER_ID},
                timeout=10
            )
            response.raise_for_status()
            conv_data = response.json()
            print(f"   ✓ Detail request successful")
            print(f"   Conversation ID: {conv_data.get('conversation_id')}")
            print(f"   Message count: {conv_data.get('message_count')}")
            print(f"   Messages:")
            for i, msg in enumerate(conv_data.get('messages', [])[:3], 1):  # Show first 3
                print(f"     {i}. Q: {msg.get('question', '')[:50]}...")
                print(f"        A: {msg.get('answer', '')[:50]}...")
        except requests.exceptions.RequestException as e:
            print(f"   ✗ Detail request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text}")
    
    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)
    print(f"\nTips:")
    print(f"1. Make sure user_id is consistent across all requests")
    print(f"2. Check server logs directory: logs/conversations_YYYY-MM-DD.jsonl")
    print(f"3. Verify the server timezone matches log file naming")
    print(f"4. Ensure the API server has write permissions to the logs directory")

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Update BASE_URL and API_KEY in this script before running!\n")
    test_conversations_api()

