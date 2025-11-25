#!/usr/bin/env python3
"""View conversation logs from logs/ directory."""

import json
import sys
from datetime import datetime
from pathlib import Path

logs_dir = Path(__file__).parent.parent / "logs"


def view_logs(date_str: str | None = None, limit: int = 10) -> None:
    """View conversation logs for a specific date or today."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    log_file = logs_dir / f"conversations_{date_str}.jsonl"
    
    if not log_file.exists():
        print(f"No logs found for {date_str}")
        return
    
    print(f"Conversation logs for {date_str}")
    print("=" * 80)
    
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines[-limit:], 1):
        try:
            entry = json.loads(line)
            user_id = entry.get('user_id', 'N/A')
            print(f"\n[{i}] {entry['timestamp']}")
            if user_id != 'N/A':
                print(f"User ID: {user_id}")
            print(f"Q: {entry['question']}")
            print(f"A: {entry['answer'][:100]}...")
            print(f"Food-related: {entry['is_food_related']} | Docs: {entry['num_retrieved_docs']} | History: {entry['history_length']}")
        except json.JSONDecodeError:
            print(f"Error parsing line {i}")
    
    print(f"\n{'='*80}")
    print(f"Showing {min(limit, len(lines))} of {len(lines)} conversations")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check if first arg is a number (limit) or date string
        try:
            limit_arg = int(sys.argv[1])
            date_arg = None
        except ValueError:
            date_arg = sys.argv[1]
            limit_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    else:
        date_arg = None
        limit_arg = 10
    
    view_logs(date_arg, limit_arg)

