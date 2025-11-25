#!/usr/bin/env python3
"""Quick test script for chatbot scope handling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.chatbot import bot


def test_question(question: str, expected_scope: str) -> None:
    """Test a single question and check scope handling."""
    print(f"\nQ: {question}")
    answer = bot.answer(question)
    print(f"A: {answer}")
    
    if expected_scope == "out-of-scope":
        answer_lower = answer.lower()
        declined = any(phrase in answer_lower for phrase in [
            "i'm vee", "culinary assistant", "food-related", 
            "cooking questions", "can't help", "only help"
        ])
        status = "✓ CORRECTLY DECLINED" if declined else "⚠ ANSWERED (should decline)"
        print(f"Status: {status}")
    else:
        print("Status: ✓ Answered (in-scope)")


if __name__ == "__main__":
    print("=" * 80)
    print("QUICK CHATBOT SCOPE TEST")
    print("=" * 80)
    
    # Out-of-scope tests
    print("\n--- OUT-OF-SCOPE QUESTIONS (Should be declined) ---")
    test_question("What's the weather today?", "out-of-scope")
    test_question("Can you write Python code?", "out-of-scope")
    test_question("What's 2 + 2?", "out-of-scope")
    
    # In-scope tests
    print("\n--- IN-SCOPE QUESTIONS (Should be answered) ---")
    test_question("What's a quick dinner recipe?", "food")
    test_question("How do I calculate calories?", "food")
    test_question("Tell me about cooking sessions", "food")
    test_question("I need a dairy-free meal", "food")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

