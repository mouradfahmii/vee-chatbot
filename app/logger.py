from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.config import settings


class ConversationLogger:
    """Logs conversation details to files in logs/ directory."""

    def __init__(self, log_dir: Path | None = None) -> None:
        self.log_dir = log_dir or Path(__file__).resolve().parents[1] / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up Python logging for application logs
        self.logger = logging.getLogger("vee_chatbot")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler if not already exists
        if not self.logger.handlers:
            log_file = self.log_dir / "app.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Also log to console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log_conversation(
        self,
        question: str,
        answer: str,
        is_food_related: bool,
        num_retrieved_docs: int = 0,
        history_length: int = 0,
        user_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a conversation turn with all relevant details."""
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "is_food_related": is_food_related,
            "num_retrieved_docs": num_retrieved_docs,
            "history_length": history_length,
            "metadata": metadata or {},
        }
        
        # Log to JSON file (one file per day)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        json_log_file = self.log_dir / f"conversations_{date_str}.jsonl"
        
        with open(json_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        # Also log to structured logger
        user_info = f"User: {user_id} | " if user_id else ""
        self.logger.info(
            f"Conversation logged | {user_info}"
            f"Food-related: {is_food_related} | "
            f"Docs: {num_retrieved_docs} | "
            f"History: {history_length} | "
            f"Q: {question[:50]}..."
        )

    def log_error(self, error: Exception, context: Optional[dict[str, Any]] = None) -> None:
        """Log errors with context."""
        self.logger.error(f"Error occurred: {error}", exc_info=True, extra=context or {})


# Global logger instance
conversation_logger = ConversationLogger()

