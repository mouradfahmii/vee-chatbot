from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    user: str
    assistant: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or command")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for maintaining context. If not provided, a new conversation is started.")
    history: Optional[List[ChatTurn]] = Field(default=None, description="DEPRECATED: Use conversation_id instead. Manual history override (for backward compatibility).")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier for logging")
    history_days: Optional[int] = Field(default=None, description="Load user's conversation history: 3 (last 3 days), 7 (last 7 days), or -1 (all history). Merged with current conversation context.")


class ImageChatRequest(BaseModel):
    question: str = Field(
        default="What is in this image? Estimate the calories.",
        description="Question about the uploaded image",
    )
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for maintaining context. If not provided, a new conversation is started.")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier for logging")


class ChatResponse(BaseModel):
    answer: str
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for this conversation. Use this in subsequent requests to maintain context.")
