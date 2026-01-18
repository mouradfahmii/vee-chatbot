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
    history_days: Optional[int] = Field(default=None, description="Load user's conversation history: 3 (last 3 days), 7 (last 7 days), or -1 (all history). Merged with current conversation context.")
    user_id: str = Field(..., description="User identifier (required for conversation history)")


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
class VoiceChatResponse(BaseModel):
    """Response model for voice chat endpoints."""
    status: int = Field(default=200, description="HTTP status code")
    message: str = Field(default="ok", description="Response message")
    transcript: str = Field(..., description="Transcribed text from user's audio input")
    data: str = Field(..., description="HTML version of the chatbot's response (converted from Markdown)")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for this conversation")
    detected_language: Optional[str] = Field(default=None, description="Detected language code (ar or en)")
    audio_base64: Optional[str] = Field(default=None, description="Base64 encoded audio response (MP3 format)")


class ConversationMessage(BaseModel):
    """Represents a single message in a conversation."""
    question: str = Field(..., description="User's question")
    answer: str = Field(..., description="Assistant's response")
    timestamp: str = Field(..., description="ISO timestamp of when the message was sent")


class ConversationSummary(BaseModel):
    """Represents a conversation summary for the list view."""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    title: str = Field(..., description="First question in the conversation (truncated to 100 chars)")
    preview: str = Field(..., description="Last message preview (truncated to 150 chars)")
    message_count: int = Field(..., description="Number of messages in the conversation")
    created_at: str = Field(..., description="ISO timestamp of when the conversation was created")
    last_updated: str = Field(..., description="ISO timestamp of the most recent message")


class ConversationListResponse(BaseModel):
    """Response model for listing conversations."""
    conversations: List[ConversationSummary] = Field(..., description="List of conversation summaries")
    total: int = Field(..., description="Total number of conversations")


class ConversationDetailResponse(BaseModel):
    """Response model for getting full conversation history."""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    user_id: str = Field(..., description="User identifier who owns this conversation")
    messages: List[ConversationMessage] = Field(..., description="List of messages in chronological order")
    created_at: str = Field(..., description="ISO timestamp of when the conversation was created")
    last_updated: str = Field(..., description="ISO timestamp of the most recent message")
    message_count: int = Field(..., description="Total number of messages in the conversation")


class HTMLChatResponse(BaseModel):
    """Response model for HTML chat endpoints."""
    status: int = Field(default=200, description="HTTP status code")
    message: str = Field(default="ok", description="Response message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for this conversation")
    data: str = Field(..., description="HTML content of the chatbot's response")
