#!/usr/bin/env python3
"""Test script to simulate conversations with the chatbot."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.chatbot import bot


def test_conversation(name: str, turns: list[dict]) -> None:
    """Run a simulated conversation and print results."""
    print(f"\n{'='*80}")
    print(f"CONVERSATION: {name}")
    print(f"{'='*80}\n")
    
    history = []
    for i, turn in enumerate(turns, 1):
        user_msg = turn["user"]
        expected_scope = turn.get("expected_scope", "food")
        
        print(f"[Turn {i}]")
        print(f"User: {user_msg}")
        print(f"Expected scope: {expected_scope}")
        
        answer = bot.answer(user_msg, history=history)
        print(f"Vee: {answer}\n")
        
        # Check if out-of-scope question was properly declined
        if expected_scope == "out-of-scope":
            answer_lower = answer.lower()
            declined_indicators = [
                "i'm vee",
                "culinary assistant",
                "food-related",
                "cooking questions",
                "can't help",
                "only help",
                "food topics"
            ]
            if any(indicator in answer_lower for indicator in declined_indicators):
                print("✓ CORRECTLY DECLINED out-of-scope question\n")
            else:
                print("⚠ WARNING: May have answered out-of-scope question\n")
        
        history.append({"user": user_msg, "assistant": answer})
        print("-" * 80)


def main() -> None:
    """Run all test conversations."""
    print("Testing Vee Food Chatbot with Simulated Conversations")
    print("=" * 80)
    
    # Test 1: In-scope food questions
    test_conversation(
        "Food & Recipe Questions",
        [
            {
                "user": "What's a quick dinner I can make in under 30 minutes?",
                "expected_scope": "food"
            },
            {
                "user": "Tell me about meal prep sessions available",
                "expected_scope": "food"
            },
            {
                "user": "I need a dairy-free meal with calorie information",
                "expected_scope": "food"
            }
        ]
    )
    
    # Test 2: Out-of-scope questions
    test_conversation(
        "Out-of-Scope Questions (Should be Declined)",
        [
            {
                "user": "What's the weather like today?",
                "expected_scope": "out-of-scope"
            },
            {
                "user": "Can you help me write Python code?",
                "expected_scope": "out-of-scope"
            },
            {
                "user": "What's 2 + 2?",
                "expected_scope": "out-of-scope"
            },
            {
                "user": "Tell me about the latest news",
                "expected_scope": "out-of-scope"
            }
        ]
    )
    
    # Test 3: Mixed conversation (in-scope and out-of-scope)
    test_conversation(
        "Mixed Conversation",
        [
            {
                "user": "How do I calculate calories from a photo?",
                "expected_scope": "food"
            },
            {
                "user": "What's the capital of France?",
                "expected_scope": "out-of-scope"
            },
            {
                "user": "Okay, can you suggest a low-glycemic meal plan?",
                "expected_scope": "food"
            }
        ]
    )
    
    # Test 4: Cooking session questions
    test_conversation(
        "Cooking Session Questions",
        [
            {
                "user": "What cooking sessions are available?",
                "expected_scope": "food"
            },
            {
                "user": "When is the gluten-free sushi rolling session?",
                "expected_scope": "food"
            },
            {
                "user": "What do I need to prepare for the meal prep session?",
                "expected_scope": "food"
            }
        ]
    )
    
    # Test 5: Edge cases
    test_conversation(
        "Edge Cases",
        [
            {
                "user": "Tell me a joke",
                "expected_scope": "out-of-scope"
            },
            {
                "user": "What ingredients are in a salad?",
                "expected_scope": "food"
            },
            {
                "user": "How do I fix my computer?",
                "expected_scope": "out-of-scope"
            }
        ]
    )
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

