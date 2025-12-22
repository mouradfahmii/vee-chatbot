from __future__ import annotations

import json
import logging
import uuid
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.config import settings

# Suppress Pydantic serialization warnings from LiteLLM
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Try to import boto3 for AWS S3 support
try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    BotoCoreError = Exception


class ConversationLogger:
    """Logs conversation details to files in logs/ directory and optionally to AWS S3."""

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
        
        # Set up AWS S3 client if configured
        self.s3_client = None
        self.s3_bucket = None
        self.s3_prefix = None
        
        if settings.aws_s3_bucket and AWS_AVAILABLE:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    region_name=settings.aws_region,
                )
                self.s3_bucket = settings.aws_s3_bucket
                self.s3_prefix = settings.aws_s3_prefix.rstrip("/")
                self.logger.info(f"AWS S3 logging enabled: s3://{self.s3_bucket}/{self.s3_prefix}/")
            except Exception as e:
                self.logger.warning(f"Failed to initialize AWS S3 client: {e}. Logs will only be stored locally.")
                self.s3_client = None
        elif settings.aws_s3_bucket and not AWS_AVAILABLE:
            self.logger.warning("AWS S3 bucket configured but boto3 not installed. Install with: pip install boto3")

    def _upload_to_s3(self, log_entry: dict[str, Any], date_str: str) -> None:
        """Upload a log entry to S3 as a separate file. Fails silently if upload fails."""
        if not self.s3_client or not self.s3_bucket:
            return
        
        try:
            # Create unique filename for each conversation
            # Format: conversations/YYYY-MM-DD/conversation_TIMESTAMP_USERID_UUID.json
            timestamp = log_entry.get("timestamp", datetime.utcnow().isoformat())
            user_id = log_entry.get("user_id") or "anonymous"
            # Create a short UUID to ensure uniqueness
            unique_id = str(uuid.uuid4())[:8]
            
            # Sanitize user_id for filename (remove special characters)
            safe_user_id = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(user_id))[:20]
            
            # Create S3 key: prefix/conversations/YYYY-MM-DD/conversation_TIMESTAMP_USERID_UUID.json
            filename = f"conversation_{timestamp.replace(':', '-').replace('.', '-')}_{safe_user_id}_{unique_id}.json"
            s3_key = f"{self.s3_prefix}/conversations/{date_str}/{filename}"
            
            # Upload the conversation as a single JSON file
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json.dumps(log_entry, ensure_ascii=False, indent=2).encode("utf-8"),
                ContentType="application/json",
            )
        except (ClientError, BotoCoreError) as e:
            # Log error but don't fail the application
            self.logger.warning(f"Failed to upload log to S3: {e}")
        except Exception as e:
            self.logger.warning(f"Unexpected error uploading log to S3: {e}")

    def log_conversation(
        self,
        question: str,
        answer: str,
        is_food_related: bool,
        num_retrieved_docs: int = 0,
        history_length: int = 0,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a conversation turn with all relevant details."""
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "conversation_id": conversation_id,
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
        
        # Upload to S3 if configured
        self._upload_to_s3(log_entry, date_str)
        
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
    
    def load_user_history_as_turns(
        self,
        user_id: str,
        days: int,
        limit: int = 1000
    ) -> List[dict[str, str]]:
        """
        Load user's past conversations from logs and convert to conversation turn format.
        
        Args:
            user_id: User identifier to filter by
            days: Number of days to look back. Use -1 for all history.
            limit: Maximum number of conversations to load (default: 1000)
            
        Returns:
            List of conversation turns in format [{"user": "...", "assistant": "..."}]
            Sorted by timestamp (oldest first)
        """
        from datetime import timedelta
        
        if not user_id:
            return []
        
        turns = []
        
        # Handle "all history" case (days = -1)
        if days == -1:
            # Load all available log files
            cutoff_date = None
            max_days_to_check = 365  # Check up to 1 year of logs
        else:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            max_days_to_check = days + 1
        
        # Iterate through log files from today backwards
        current_date = datetime.utcnow()
        checked_dates = set()
        
        for _ in range(max_days_to_check):  # Include today
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Skip if we've already checked this date
            if date_str in checked_dates:
                current_date -= timedelta(days=1)
                continue
            checked_dates.add(date_str)
            
            log_file = self.log_dir / f"conversations_{date_str}.jsonl"
            
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                entry_user_id = entry.get("user_id")
                                
                                # Filter by user_id
                                if entry_user_id == user_id:
                                    # Parse timestamp and check if within range
                                    try:
                                        entry_timestamp_str = entry.get("timestamp", "")
                                        # Handle both with and without timezone
                                        if "Z" in entry_timestamp_str:
                                            entry_timestamp = datetime.fromisoformat(
                                                entry_timestamp_str.replace("Z", "+00:00")
                                            )
                                        else:
                                            entry_timestamp = datetime.fromisoformat(entry_timestamp_str)
                                        
                                        # Convert to UTC if needed
                                        if entry_timestamp.tzinfo is not None:
                                            entry_timestamp = entry_timestamp.replace(tzinfo=None)
                                        
                                        # If cutoff_date is None (all history), include all entries
                                        # Otherwise, check if entry is within date range
                                        if cutoff_date is None or entry_timestamp >= cutoff_date:
                                            turns.append({
                                                "user": entry.get("question", ""),
                                                "assistant": entry.get("answer", ""),
                                                "timestamp": entry_timestamp_str,
                                            })
                                    except (ValueError, KeyError) as e:
                                        # Skip entries with invalid timestamps
                                        continue
                            except (json.JSONDecodeError, KeyError) as e:
                                # Skip malformed entries
                                continue
                except Exception as e:
                    self.logger.warning(f"Error reading log file {log_file}: {e}")
            
            current_date -= timedelta(days=1)
            # Stop if we've gone past the cutoff date (unless loading all history)
            if cutoff_date is not None and current_date < cutoff_date:
                break
            # Stop if we've checked enough days (for all history, stop after reasonable limit)
            if days == -1 and len(checked_dates) >= max_days_to_check:
                break
        
        # Sort by timestamp (oldest first) and limit results
        try:
            turns.sort(key=lambda x: x.get("timestamp", ""))
        except Exception:
            # If sorting fails, just return as-is
            pass
        
        return turns[:limit]


# Global logger instance
conversation_logger = ConversationLogger()

