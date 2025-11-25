from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.chatbot import bot
from app.ingest import ingest_dataset
from api.schemas import ChatRequest, ChatResponse, ImageChatRequest

app = FastAPI(title="Vee Food Chatbot", version="0.1.0")


@app.on_event("startup")
async def ensure_chroma_seeded() -> None:
    try:
        ingest_dataset(reset=False)
    except FileNotFoundError as exc:
        raise RuntimeError("Missing synthetic dataset. Did you create data/?") from exc


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        answer = bot.answer(payload.message, history=payload.history, user_id=payload.user_id)
    except Exception as exc:  # pragma: no cover - propagate LLM errors with context
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ChatResponse(answer=answer)


@app.post("/chat/image", response_model=ChatResponse)
async def chat_image_endpoint(
    image: UploadFile = File(..., description="Food image to analyze"),
    question: str = "What is in this image? Estimate the calories.",
    user_id: str | None = None,
) -> ChatResponse:
    """Analyze a food image and answer questions about it."""
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Analyze image
        answer = bot.answer_with_image(image_data, question=question, user_id=user_id)
        return ChatResponse(answer=answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ingest")
async def reingest(reset: bool = True) -> dict:
    count = ingest_dataset(reset=reset)
    return {"documents": count, "reset": reset}
