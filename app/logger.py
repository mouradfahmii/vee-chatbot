from __future__ import annotations

import json
import logging
import uuid
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

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
        
        # Extract image_url from metadata if present
        image_url = None
        if metadata:
            image_url = metadata.get("image_url")
        
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
        
        # Add image_url to log entry if present
        if image_url:
            log_entry["image_url"] = image_url
        
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
                                
                                # Filter by user_id - normalize for comparison
                                entry_user_id_str = str(entry_user_id).strip() if entry_user_id else None
                                user_id_str = str(user_id).strip()
                                
                                if entry_user_id_str == user_id_str:
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

    def list_user_conversations(self, user_id: str, max_conversations: int = 100) -> List[dict[str, Any]]:
        """
        List all conversations for a user, grouped by conversation_id.
        
        Args:
            user_id: User identifier to filter by
            max_conversations: Maximum number of conversations to return (default: 100)
            
        Returns:
            List of conversation summaries with:
            - conversation_id: str
            - title: str (first question, truncated to 100 chars)
            - preview: str (last message preview, truncated to 150 chars)
            - message_count: int
            - created_at: str (ISO timestamp)
            - last_updated: str (ISO timestamp)
            Sorted by last_updated (most recent first)
        """
        from datetime import timedelta
        
        if not user_id:
            return []
        
        # Dictionary to group conversations by conversation_id
        conversations: dict[str, dict[str, Any]] = {}
        
        # Check up to 1 year of logs
        max_days_to_check = 365
        current_date = datetime.utcnow()
        checked_dates = set()
        
        for _ in range(max_days_to_check):
            date_str = current_date.strftime("%Y-%m-%d")
            
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
                                entry_conversation_id = entry.get("conversation_id")
                                
                                # Filter by user_id and ensure conversation_id exists
                                # Normalize values for comparison
                                entry_user_id_str = str(entry_user_id).strip() if entry_user_id else None
                                user_id_str = str(user_id).strip()
                                
                                if entry_user_id_str == user_id_str and entry_conversation_id:
                                    # Normalize conversation_id for consistent grouping
                                    entry_conv_id_str = str(entry_conversation_id).strip()
                                    
                                    # Initialize conversation if not exists
                                    if entry_conv_id_str not in conversations:
                                        conversations[entry_conv_id_str] = {
                                            "conversation_id": entry_conv_id_str,
                                            "title": "",
                                            "preview": "",
                                            "message_count": 0,
                                            "created_at": entry.get("timestamp", ""),
                                            "last_updated": entry.get("timestamp", ""),
                                        }
                                    
                                    conv = conversations[entry_conv_id_str]
                                    entry_timestamp = entry.get("timestamp", "")
                                    
                                    # Update first question as title (if not set yet)
                                    question = entry.get("question", "")
                                    if not conv["title"] and question:
                                        # Truncate to 100 characters
                                        conv["title"] = question[:100] + ("..." if len(question) > 100 else "")
                                    
                                    # Update preview with last question or answer
                                    if question:
                                        preview_text = question
                                    else:
                                        preview_text = entry.get("answer", "")
                                    
                                    if preview_text:
                                        # Truncate to 150 characters
                                        conv["preview"] = preview_text[:150] + ("..." if len(preview_text) > 150 else "")
                                    
                                    # Update timestamps
                                    if entry_timestamp:
                                        # Update created_at if this is earlier
                                        try:
                                            if "Z" in entry_timestamp:
                                                entry_dt = datetime.fromisoformat(entry_timestamp.replace("Z", "+00:00"))
                                            else:
                                                entry_dt = datetime.fromisoformat(entry_timestamp)
                                            
                                            if entry_dt.tzinfo is not None:
                                                entry_dt = entry_dt.replace(tzinfo=None)
                                            
                                            # Parse existing timestamps for comparison
                                            if conv["created_at"]:
                                                if "Z" in conv["created_at"]:
                                                    created_dt = datetime.fromisoformat(conv["created_at"].replace("Z", "+00:00"))
                                                else:
                                                    created_dt = datetime.fromisoformat(conv["created_at"])
                                                if created_dt.tzinfo is not None:
                                                    created_dt = created_dt.replace(tzinfo=None)
                                                
                                                if entry_dt < created_dt:
                                                    conv["created_at"] = entry_timestamp
                                            
                                            # Update last_updated if this is later
                                            if conv["last_updated"]:
                                                if "Z" in conv["last_updated"]:
                                                    last_dt = datetime.fromisoformat(conv["last_updated"].replace("Z", "+00:00"))
                                                else:
                                                    last_dt = datetime.fromisoformat(conv["last_updated"])
                                                if last_dt.tzinfo is not None:
                                                    last_dt = last_dt.replace(tzinfo=None)
                                                
                                                if entry_dt > last_dt:
                                                    conv["last_updated"] = entry_timestamp
                                        except (ValueError, KeyError):
                                            # If timestamp parsing fails, keep existing values
                                            pass
                                    
                                    # Increment message count
                                    conv["message_count"] += 1
                                    
                            except (json.JSONDecodeError, KeyError):
                                # Skip malformed entries
                                continue
                except Exception as e:
                    self.logger.warning(f"Error reading log file {log_file}: {e}")
            
            current_date -= timedelta(days=1)
            # Stop after checking enough days
            if len(checked_dates) >= max_days_to_check:
                break
        
        # Convert to list and sort by last_updated (most recent first)
        conversation_list = list(conversations.values())
        try:
            conversation_list.sort(
                key=lambda x: x.get("last_updated", ""),
                reverse=True
            )
        except Exception:
            # If sorting fails, just return as-is
            pass
        
        return conversation_list[:max_conversations]

    def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str
    ) -> List[dict[str, str]]:
        """
        Get full conversation history for a specific conversation_id.
        Security: Only returns conversations that match both conversation_id AND user_id.
        
        Args:
            conversation_id: Conversation identifier to filter by
            user_id: User identifier to filter by (for security)
            
        Returns:
            List of messages in format:
            [
                {
                    "question": str,
                    "answer": str,
                    "timestamp": str (ISO timestamp)
                },
                ...
            ]
            Sorted by timestamp (oldest first)
            Returns empty list if conversation not found or user_id doesn't match
        """
        from datetime import timedelta
        
        if not conversation_id or not user_id:
            return []
        
        messages = []
        
        # Check up to 1 year of logs
        max_days_to_check = 365
        current_date = datetime.utcnow()
        checked_dates = set()
        
        for _ in range(max_days_to_check):
            date_str = current_date.strftime("%Y-%m-%d")
            
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
                                entry_conversation_id = entry.get("conversation_id")
                                
                                # Filter by both conversation_id AND user_id (security)
                                # Normalize values: convert to string and strip whitespace
                                entry_user_id_str = str(entry_user_id).strip() if entry_user_id else None
                                entry_conv_id_str = str(entry_conversation_id).strip() if entry_conversation_id else None
                                user_id_str = str(user_id).strip()
                                conv_id_str = str(conversation_id).strip()
                                
                                # Match if both user_id and conversation_id match
                                if entry_user_id_str == user_id_str and entry_conv_id_str == conv_id_str:
                                    message_dict = {
                                        "question": entry.get("question", ""),
                                        "answer": entry.get("answer", ""),
                                        "timestamp": entry.get("timestamp", ""),
                                    }
                                    # Add image_url if present
                                    if entry.get("image_url"):
                                        message_dict["image_url"] = entry.get("image_url")
                                    messages.append(message_dict)
                                    
                            except (json.JSONDecodeError, KeyError):
                                # Skip malformed entries
                                continue
                except Exception as e:
                    self.logger.warning(f"Error reading log file {log_file}: {e}")
            
            current_date -= timedelta(days=1)
            # Stop after checking enough days
            if len(checked_dates) >= max_days_to_check:
                break
        
        # Sort by timestamp (oldest first)
        try:
            messages.sort(key=lambda x: x.get("timestamp", ""))
        except Exception:
            # If sorting fails, just return as-is
            pass
        
        return messages


# Global logger instance
conversation_logger = ConversationLogger()

