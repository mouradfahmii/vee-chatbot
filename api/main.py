from __future__ import annotations

import html
import re
import uuid

import base64

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from app.chatbot import bot
from app.config import settings
from app.conversation_manager import conversation_manager
from app.ingest import ingest_dataset
from app.mysql_ingestor import ingest_mysql
from app.voice_utils import get_voice_processor
from api.auth import verify_api_key
from api.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessage,
    ConversationSummary,
    HTMLChatResponse,
    ImageChatRequest,
    VoiceChatResponse,
)

app = FastAPI(title="Vee Food Chatbot", version="0.1.0")


def markdown_to_html(text: str) -> str:
    """
    Convert Markdown formatting to HTML.
    Converts headers (#, ##, ###), bold (**text**), and italic (*text*) to HTML.
    """
    # Convert Markdown headers to HTML
    # ### Header -> <h3>Header</h3>
    html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    # ## Header -> <h2>Header</h2>
    html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    # # Header -> <h1>Header</h1>
    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    
    # Convert bold (**text**)
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
    
    # Convert italic (*text*)
    html_content = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', html_content)
    
    # Escape HTML and convert newlines
    safe_html = html.escape(html_content).replace("\n", "<br>")
    
    # Unescape our HTML tags
    safe_html = safe_html.replace("&lt;h1&gt;", "<h1>").replace("&lt;/h1&gt;", "</h1>")
    safe_html = safe_html.replace("&lt;h2&gt;", "<h2>").replace("&lt;/h2&gt;", "</h2>")
    safe_html = safe_html.replace("&lt;h3&gt;", "<h3>").replace("&lt;/h3&gt;", "</h3>")
    safe_html = safe_html.replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
    safe_html = safe_html.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
    
    return safe_html


@app.on_event("startup")
async def ensure_chroma_seeded() -> None:
    """Load knowledge base on startup."""
    from app.config import settings
    
    try:
        # Always load JSON data if available
        ingest_dataset(reset=False)
    except FileNotFoundError:
        # JSON file is optional if MySQL is used
        pass
    
    # Optionally load MySQL data on startup
    if settings.ingest_mysql_on_startup:
        try:
            ingest_mysql(reset=False)
        except Exception as e:
            # Log but don't fail startup if MySQL ingestion fails
            import logging
            logging.warning(f"MySQL ingestion on startup failed: {e}")


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key),
) -> ChatResponse:
    """Chat endpoint - requires API key authentication."""
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Generate conversation_id if not provided
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    
    # Get conversation history (use manual history if provided for backward compatibility, otherwise use conversation manager)
    if payload.history is not None:
        # Backward compatibility: use provided history
        history = [{"user": turn.user, "assistant": turn.assistant} for turn in payload.history]
    else:
        # Use conversation manager to get history
        history_turns = conversation_manager.get_history(conversation_id)
        history = [{"user": turn.user, "assistant": turn.assistant} for turn in history_turns]
    
    try:
        answer = bot.answer(
            payload.message, 
            history=history if history else None, 
            user_id=payload.user_id,
            conversation_id=conversation_id
        )
        
        # Store the conversation turn
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_message=payload.message,
            assistant_message=answer,
            user_id=payload.user_id,
        )
    except Exception as exc:  # pragma: no cover - propagate LLM errors with context
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    
    return ChatResponse(answer=answer, conversation_id=conversation_id)


@app.post(
    "/chat/html",
    response_model=HTMLChatResponse,
    responses={200: {"content": {"application/json": {}}}},
)
async def chat_html_endpoint(
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key),
) -> HTMLChatResponse:
    """
    Chat endpoint that returns HTML instead of JSON.
    Converts Markdown headers (#, ##, ###) and formatting (*, **) to HTML.
    """
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Generate conversation_id if not provided
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    
    # Get conversation history (use manual history if provided for backward compatibility, otherwise use conversation manager)
    if payload.history is not None:
        # Backward compatibility: use provided history
        history = [{"user": turn.user, "assistant": turn.assistant} for turn in payload.history]
    else:
        # Use conversation manager to get history
        history_turns = conversation_manager.get_history(conversation_id)
        history = [{"user": turn.user, "assistant": turn.assistant} for turn in history_turns]
    
    # Load historical conversations from logs if history_days is specified
    if payload.history_days is not None and payload.user_id:
        from app.logger import conversation_logger
        # Validate history_days: must be 3, 7, or -1 (all history)
        if payload.history_days not in [3, 7, -1]:
            raise HTTPException(
                status_code=400, 
                detail="history_days must be 3 (last 3 days), 7 (last 7 days), or -1 (all history)"
            )
        historical_turns = conversation_logger.load_user_history_as_turns(
            user_id=payload.user_id,
            days=payload.history_days
        )
        # Merge historical turns with current conversation history
        # Historical turns are already sorted oldest first, so prepend them
        history = historical_turns + history
    
    try:
        answer = bot.answer(
            payload.message, 
            history=history if history else None, 
            user_id=payload.user_id,
            conversation_id=conversation_id
        )
        
        # Store the conversation turn
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_message=payload.message,
            assistant_message=answer,
            user_id=payload.user_id,
        )
    except Exception as exc:  # pragma: no cover - propagate LLM errors with context
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    safe_html = markdown_to_html(answer)
    return HTMLChatResponse(
        status=200,
        message="ok",
        conversation_id=conversation_id,
        data=safe_html
    )


@app.post("/chat/image", response_model=ChatResponse)
async def chat_image_endpoint(
    image: UploadFile = File(..., description="Food image to analyze"),
    question: str = "What is in this image? Estimate the calories.",
    conversation_id: str | None = None,
    user_id: str | None = None,
    api_key: str = Depends(verify_api_key),
) -> ChatResponse:
    """Analyze a food image and answer questions about it - requires API key authentication."""
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate conversation_id if not provided
    conversation_id = conversation_id or str(uuid.uuid4())
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Analyze image
        answer = bot.answer_with_image(
            image_data, 
            question=question, 
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # Store the conversation turn (even though image analysis doesn't use history, 
        # we store it so follow-up questions can reference previous analyses)
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_message=f"[IMAGE] {question}",
            assistant_message=answer,
            user_id=user_id,
        )
        
        return ChatResponse(answer=answer, conversation_id=conversation_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/chat/image/html",
    response_model=HTMLChatResponse,
    responses={200: {"content": {"application/json": {}}}},
)
async def chat_image_html_endpoint(
    image: UploadFile = File(..., description="Food image to analyze"),
    question: str = "What is in this image? Estimate the calories.",
    conversation_id: str | None = None,
    user_id: str | None = None,
    api_key: str = Depends(verify_api_key),
) -> HTMLChatResponse:
    """
    Analyze a food image and return HTML response.
    Converts Markdown headers (#, ##, ###) and formatting (*, **) to HTML.
    """
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate conversation_id if not provided
    conversation_id = conversation_id or str(uuid.uuid4())
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Analyze image
        answer = bot.answer_with_image(
            image_data, 
            question=question, 
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # Store the conversation turn (even though image analysis doesn't use history, 
        # we store it so follow-up questions can reference previous analyses)
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_message=f"[IMAGE] {question}",
            assistant_message=answer,
            user_id=user_id,
        )
        
        # Convert Markdown to HTML
        safe_html = markdown_to_html(answer)
        return HTMLChatResponse(
            status=200,
            message="ok",
            conversation_id=conversation_id,
            data=safe_html
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ingest")
async def reingest(
    reset: bool = True,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Reingest the knowledge base from JSON file - requires API key authentication (admin endpoint)."""
    count = ingest_dataset(reset=reset)
    return {"documents": count, "reset": reset, "source": "json"}


@app.post("/ingest/mysql")
async def reingest_mysql(
    reset: bool = False,
    tables: str | None = None,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Ingest MySQL database into knowledge base - requires API key authentication (admin endpoint).
    
    Args:
        reset: If True, reset the vector store before adding MySQL data
        tables: Comma-separated list of table names to ingest. If None, ingests all tables.
    """
    table_list = [t.strip() for t in tables.split(",")] if tables else None
    count = ingest_mysql(reset=reset, table_names=table_list)
    return {
        "documents": count,
        "reset": reset,
        "source": "mysql",
        "tables": table_list or "all"
    }


@app.post("/chat/voice", response_model=VoiceChatResponse)
async def chat_voice_endpoint(
    audio: UploadFile = File(..., description="Audio file (WebM or MP3) containing user's voice message"),
    conversation_id: str | None = None,
    user_id: str | None = None,
    history_days: int | None = None,
    api_key: str = Depends(verify_api_key),
) -> VoiceChatResponse:
    """
    Voice chat endpoint - accepts audio input and returns audio response.
    Supports Arabic and English - responds in the same language as input.
    """
    from app.logger import conversation_logger
    
    # Generate conversation_id if not provided
    conversation_id = conversation_id or str(uuid.uuid4())
    
    # Validate audio format
    try:
        voice_processor = get_voice_processor()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice processor initialization failed: {str(e)}")
    
    is_valid, audio_format = voice_processor.validate_audio_format(audio.content_type, audio.filename)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported formats: WebM, MP3, WAV, M4A, OGG"
        )
    
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Validate audio size
        if not voice_processor.validate_audio_size(audio_data, max_size_mb=settings.max_audio_size_mb):
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large. Maximum size: {settings.max_audio_size_mb}MB"
            )
        
        # Convert speech to text
        transcript, detected_language = voice_processor.speech_to_text(audio_data, audio_format)
        
        if not transcript or not transcript.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio. Please ensure audio contains clear speech.")
        
        # Get conversation history (similar to text endpoints)
        history_turns = conversation_manager.get_history(conversation_id)
        history = [{"user": turn.user, "assistant": turn.assistant} for turn in history_turns]
        
        # Load historical conversations from logs if history_days is specified
        if history_days is not None and user_id:
            # Validate history_days: must be 3, 7, or -1 (all history)
            if history_days not in [3, 7, -1]:
                raise HTTPException(
                    status_code=400,
                    detail="history_days must be 3 (last 3 days), 7 (last 7 days), or -1 (all history)"
                )
            historical_turns = conversation_logger.load_user_history_as_turns(
                user_id=user_id,
                days=history_days
            )
            # Merge historical turns with current conversation history
            history = historical_turns + history
        
        # Process through chatbot
        answer_markdown = bot.answer(
            transcript,
            history=history if history else None,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # Convert Markdown to HTML for data field
        answer_text_html = markdown_to_html(answer_markdown)
        
        # Store the conversation turn (store original markdown for consistency)
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_message=transcript,
            assistant_message=answer_markdown,
            user_id=user_id,
        )
        
        # Convert text response to speech (use original markdown, not HTML)
        # Use detected language to ensure voice matches
        audio_base64 = None
        try:
            audio_response = voice_processor.text_to_speech(
                text=answer_markdown,
                language=detected_language,
                voice=settings.tts_voice,
                model=settings.tts_model,
            )
            audio_base64 = base64.b64encode(audio_response).decode("utf-8")
        except Exception as tts_error:
            # If TTS fails, still return the text response
            # Log the error but don't fail the request
            import logging
            logging.warning(f"TTS conversion failed: {tts_error}")
        
        return VoiceChatResponse(
            status=200,
            message="ok",
            transcript=transcript,
            data=answer_text_html,
            conversation_id=conversation_id,
            detected_language=detected_language,
            audio_base64=audio_base64,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Voice processing error: {str(exc)}") from exc


@app.post("/chat/voice/text", response_model=VoiceChatResponse)
async def chat_voice_text_endpoint(
    audio: UploadFile = File(..., description="Audio file (WebM or MP3) containing user's voice message"),
    conversation_id: str | None = None,
    user_id: str | None = None,
    history_days: int | None = None,
    api_key: str = Depends(verify_api_key),
) -> VoiceChatResponse:
    """
    Voice chat endpoint that returns text response instead of audio (for debugging/preview).
    Accepts audio input, processes it, but returns JSON with text response only.
    """
    from app.logger import conversation_logger
    
    # Generate conversation_id if not provided
    conversation_id = conversation_id or str(uuid.uuid4())
    
    # Validate audio format
    try:
        voice_processor = get_voice_processor()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice processor initialization failed: {str(e)}")
    
    is_valid, audio_format = voice_processor.validate_audio_format(audio.content_type, audio.filename)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported formats: WebM, MP3, WAV, M4A, OGG"
        )
    
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Validate audio size
        if not voice_processor.validate_audio_size(audio_data, max_size_mb=settings.max_audio_size_mb):
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large. Maximum size: {settings.max_audio_size_mb}MB"
            )
        
        # Convert speech to text
        transcript, detected_language = voice_processor.speech_to_text(audio_data, audio_format)
        
        if not transcript or not transcript.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio. Please ensure audio contains clear speech.")
        
        # Get conversation history
        history_turns = conversation_manager.get_history(conversation_id)
        history = [{"user": turn.user, "assistant": turn.assistant} for turn in history_turns]
        
        # Load historical conversations from logs if history_days is specified
        if history_days is not None and user_id:
            if history_days not in [3, 7, -1]:
                raise HTTPException(
                    status_code=400,
                    detail="history_days must be 3 (last 3 days), 7 (last 7 days), or -1 (all history)"
                )
            historical_turns = conversation_logger.load_user_history_as_turns(
                user_id=user_id,
                days=history_days
            )
            history = historical_turns + history
        
        # Process through chatbot
        # The bot.answer() method already logs the conversation, so we don't need to log again
        answer_markdown = bot.answer(
            transcript,
            history=history if history else None,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # Convert Markdown to HTML for data field
        answer_text_html = markdown_to_html(answer_markdown)
        
        # Store the conversation turn (store original markdown for consistency)
        conversation_manager.add_turn(
            conversation_id=conversation_id,
            user_message=transcript,
            assistant_message=answer_markdown,
            user_id=user_id,
        )
        
        # Return text response only (no audio)
        return VoiceChatResponse(
            status=200,
            message="ok",
            transcript=transcript,
            data=answer_text_html,
            conversation_id=conversation_id,
            detected_language=detected_language,
            audio_base64=None,  # No audio for text endpoint
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Voice processing error: {str(exc)}") from exc


@app.get("/conversations", response_model=ConversationListResponse)
async def list_conversations_endpoint(
    user_id: str,
    api_key: str = Depends(verify_api_key),
) -> ConversationListResponse:
    """
    List all conversations for a user.
    Returns conversation summaries sorted by last_updated (most recent first).
    Maximum 100 conversations returned.
    """
    from app.logger import conversation_logger
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    try:
        conversations_dict = conversation_logger.list_user_conversations(user_id=user_id, max_conversations=100)
        
        # Convert dicts to ConversationSummary models
        conversations = [ConversationSummary(**conv) for conv in conversations_dict]
        
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(exc)}") from exc


@app.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_endpoint(
    conversation_id: str,
    user_id: str,
    api_key: str = Depends(verify_api_key),
) -> ConversationDetailResponse:
    """
    Get full conversation history for a specific conversation.
    Security: Only returns conversations that match both conversation_id AND user_id.
    Returns 404 if conversation not found or user_id doesn't match.
    """
    from app.logger import conversation_logger
    
    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    try:
        messages = conversation_logger.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        
        if not messages:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or you don't have access to it"
            )
        
        # Extract metadata from messages
        created_at = messages[0]["timestamp"] if messages else ""
        last_updated = messages[-1]["timestamp"] if messages else ""
        message_count = len(messages)
        
        # Convert dicts to ConversationMessage models
        message_models = [ConversationMessage(**msg) for msg in messages]
        
        return ConversationDetailResponse(
            conversation_id=conversation_id,
            user_id=user_id,
            messages=message_models,
            created_at=created_at,
            last_updated=last_updated,
            message_count=message_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(exc)}") from exc
