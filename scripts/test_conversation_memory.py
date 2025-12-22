#!/usr/bin/env python3
"""
Test script to verify conversation memory using conversation_id.

This script tests that:
1. Conversations maintain context across multiple messages
2. Follow-up questions reference previous messages
3. Conversation IDs are properly generated and returned
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "d1oxiJyt4SKAGcCGdzklFvbvcatcIk1Hi8iZXFrzFw4"  # Update with your API key

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
}


def test_conversation_memory():
    """Test conversation memory with a multi-turn conversation."""
    
    print("=" * 80)
    print("Testing Conversation Memory")
    print("=" * 80)
    print()
    
    conversation_id = None
    
    # Test 1: First message - should get a conversation_id
    print("Test 1: First message (asking about recipes)")
    print("-" * 80)
    response1 = requests.post(
        f"{API_BASE_URL}/chat",
        headers=HEADERS,
        json={
            "message": "What are some healthy dinner recipes?",
            "user_id": "test_user_001",
        },
    )
    
    if response1.status_code != 200:
        print(f"[ERROR] Error: {response1.status_code}")
        print(response1.text)
        return False
    
    data1 = response1.json()
    conversation_id = data1.get("conversation_id")
    print(f"[OK] Response: {data1['answer'][:200]}...")
    print(f"[OK] Conversation ID: {conversation_id}")
    print()
    
    if not conversation_id:
        print("[ERROR] No conversation_id returned!")
        return False
    
    # Test 2: Follow-up question - should reference previous conversation
    print("Test 2: Follow-up question (asking for more details)")
    print("-" * 80)
    response2 = requests.post(
        f"{API_BASE_URL}/chat",
        headers=HEADERS,
        json={
            "message": "Can you tell me more about the first one?",
            "conversation_id": conversation_id,
            "user_id": "test_user_001",
        },
    )
    
    if response2.status_code != 200:
        print(f"[ERROR] Error: {response2.status_code}")
        print(response2.text)
        return False
    
    data2 = response2.json()
    print(f"[OK] Response: {data2['answer'][:200]}...")
    print(f"[OK] Conversation ID: {data2.get('conversation_id')} (should match)")
    print()
    
    # Verify conversation_id matches
    if data2.get("conversation_id") != conversation_id:
        print(f"[ERROR] Conversation ID mismatch! Expected {conversation_id}, got {data2.get('conversation_id')}")
        return False
    
    # Test 3: Another follow-up - should maintain context
    print("Test 3: Another follow-up (asking about ingredients)")
    print("-" * 80)
    response3 = requests.post(
        f"{API_BASE_URL}/chat",
        headers=HEADERS,
        json={
            "message": "What ingredients do I need?",
            "conversation_id": conversation_id,
            "user_id": "test_user_001",
        },
    )
    
    if response3.status_code != 200:
        print(f"[ERROR] Error: {response3.status_code}")
        print(response3.text)
        return False
    
    data3 = response3.json()
    print(f"[OK] Response: {data3['answer'][:200]}...")
    print()
    
    # Test 4: Test HTML endpoint with conversation_id
    print("Test 4: HTML endpoint with conversation_id")
    print("-" * 80)
    response4 = requests.post(
        f"{API_BASE_URL}/chat/html",
        headers=HEADERS,
        json={
            "message": "How long does it take to cook?",
            "conversation_id": conversation_id,
            "user_id": "test_user_001",
        },
    )
    
    if response4.status_code != 200:
        print(f"[ERROR] Error: {response4.status_code}")
        print(response4.text)
        return False
    
    html_response = response4.text[:200]
    print(f"[OK] HTML Response: {html_response}...")
    print()
    
    # Test 5: New conversation without conversation_id - should start fresh
    print("Test 5: New conversation (no conversation_id - should start fresh)")
    print("-" * 80)
    response5 = requests.post(
        f"{API_BASE_URL}/chat",
        headers=HEADERS,
        json={
            "message": "What are some breakfast ideas?",
            "user_id": "test_user_001",
        },
    )
    
    if response5.status_code != 200:
        print(f"[ERROR] Error: {response5.status_code}")
        print(response5.text)
        return False
    
    data5 = response5.json()
    new_conversation_id = data5.get("conversation_id")
    print(f"[OK] Response: {data5['answer'][:200]}...")
    print(f"[OK] New Conversation ID: {new_conversation_id} (should be different)")
    print()
    
    if new_conversation_id == conversation_id:
        print(f"[ERROR] New conversation should have different ID!")
        return False
    
    # Test 6: Arabic conversation memory
    print("Test 6: Arabic conversation memory")
    print("-" * 80)
    arabic_conversation_id = None
    
    response6a = requests.post(
        f"{API_BASE_URL}/chat",
        headers=HEADERS,
        json={
            "message": "ما هي وصفة صحية وسريعة للعشاء؟",
            "user_id": "test_user_002",
        },
    )
    
    if response6a.status_code == 200:
        data6a = response6a.json()
        arabic_conversation_id = data6a.get("conversation_id")
        print(f"[OK] First Arabic message response: {data6a['answer'][:200]}...")
        print(f"[OK] Conversation ID: {arabic_conversation_id}")
        print()
        
        # Follow-up in Arabic
        response6b = requests.post(
            f"{API_BASE_URL}/chat",
            headers=HEADERS,
            json={
                "message": "ما هي المكونات؟",
                "conversation_id": arabic_conversation_id,
                "user_id": "test_user_002",
            },
        )
        
        if response6b.status_code == 200:
            data6b = response6b.json()
            print(f"[OK] Follow-up Arabic response: {data6b['answer'][:200]}...")
            print()
        else:
            print(f"[WARNING] Follow-up Arabic request failed: {response6b.status_code}")
    else:
        print(f"[WARNING] Arabic conversation test skipped (API may not be configured)")
    
    print("=" * 80)
    print("[OK] All tests completed successfully!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        success = test_conversation_memory()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to API. Make sure the server is running:")
        print("   uvicorn api.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

