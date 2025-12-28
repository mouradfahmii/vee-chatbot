#!/usr/bin/env python3
"""Debug script to check conversation logs and list_user_conversations."""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logger import ConversationLogger

def main():
    logger = ConversationLogger()
    
    print("=" * 60)
    print("DEBUG: Conversation Logging")
    print("=" * 60)
    
    # Check log directory
    print(f"\n1. Log directory: {logger.log_dir}")
    print(f"   Exists: {logger.log_dir.exists()}")
    
    # Check today's log file
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_file = logger.log_dir / f"conversations_{today}.jsonl"
    print(f"\n2. Today's log file: {log_file}")
    print(f"   Exists: {log_file.exists()}")
    
    # List all log files
    log_files = list(logger.log_dir.glob("conversations_*.jsonl"))
    print(f"\n3. All log files found: {len(log_files)}")
    for f in sorted(log_files)[-5:]:  # Show last 5
        print(f"   - {f.name} ({f.stat().st_size} bytes)")
    
    # Read and display recent entries
    if log_files:
        print(f"\n4. Reading entries from most recent log file...")
        latest_file = max(log_files, key=lambda f: f.stat().st_mtime)
        print(f"   File: {latest_file.name}")
        
        entries = []
        with open(latest_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
        
        print(f"   Total entries: {len(entries)}")
        
        if entries:
            print(f"\n5. Sample entries (last 3):")
            for i, entry in enumerate(entries[-3:], 1):
                print(f"\n   Entry {i}:")
                print(f"     user_id: {repr(entry.get('user_id'))}")
                print(f"     conversation_id: {repr(entry.get('conversation_id'))}")
                question = entry.get('question', '')
                question_preview = question[:50] if question else ''
                print(f"     question: {question_preview}...")
                print(f"     timestamp: {entry.get('timestamp')}")
        
        # Test list_user_conversations with different user_ids
        print(f"\n6. Testing list_user_conversations...")
        
        # Get unique user_ids from logs
        user_ids = set()
        for entry in entries:
            user_id = entry.get("user_id")
            if user_id:
                user_ids.add(user_id)
        
        print(f"   Unique user_ids found in logs: {sorted(user_ids) if user_ids else 'None (all entries have user_id=None)'}")
        
        if user_ids:
            for user_id in sorted(user_ids):
                print(f"\n   Testing with user_id: {repr(user_id)}")
                conversations = logger.list_user_conversations(user_id=user_id, max_conversations=10)
                print(f"   Found {len(conversations)} conversations")
                for conv in conversations[:3]:  # Show first 3
                    print(f"     - {conv.get('conversation_id')}: {conv.get('title', '')[:50]}")
        else:
            print(f"\n   ⚠️  WARNING: No user_id found in any log entries!")
            print(f"   This means list_user_conversations will return empty results.")
            print(f"   Make sure to include 'user_id' in your chat requests.")
            
            # Test with None
            print(f"\n   Testing with user_id=None (should return empty):")
            conversations = logger.list_user_conversations(user_id=None, max_conversations=10)
            print(f"   Found {len(conversations)} conversations (expected: 0)")
    
    else:
        print(f"\n4. ⚠️  No log files found!")
        print(f"   This means no conversations have been logged yet.")
        print(f"   Make a chat request first to create log entries.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

