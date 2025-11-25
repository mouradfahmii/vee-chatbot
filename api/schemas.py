from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    user: str
    assistant: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or command")
    history: Optional[List[ChatTurn]] = Field(default=None)
    user_id: Optional[str] = Field(default=None, description="Optional user identifier for logging")


class ImageChatRequest(BaseModel):
    question: str = Field(
        default="What is in this image? Estimate the calories.",
        description="Question about the uploaded image",
    )
    user_id: Optional[str] = Field(default=None, description="Optional user identifier for logging")


class ChatResponse(BaseModel):
    answer: str
