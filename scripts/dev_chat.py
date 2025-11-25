#!/usr/bin/env python3
"""Simple REPL to talk to the chatbot without running the API."""

from app.chatbot import bot


def main() -> None:
    print("Vee Food Chatbot — type 'exit' to quit")
    history = []
    while True:
        try:
            question = input("You: ")
        except EOFError:
            break
        if question.strip().lower() in {"exit", "quit"}:
            break
        answer = bot.answer(question, history=history)
        print(f"Vee: {answer}\n")
        history.append({"user": question, "assistant": answer})


if __name__ == "__main__":
    main()
