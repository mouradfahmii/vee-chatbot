# API Guide: Chat History & Voice Chat

This guide provides comprehensive examples for using the chat history and voice chat features of the Vee Food Chatbot API.

---

## Table of Contents

1. [Chat History API](#chat-history-api)
   - [No History (Default)](#no-history-default)
   - [3 Days History](#3-days-history)
   - [7 Days History](#7-days-history)
   - [All History](#all-history)
2. [Voice Chat API](#voice-chat-api)
   - [Voice Input → Voice Output](#voice-input--voice-output)
   - [Voice Input → Text Output](#voice-input--text-output)
   - [Voice Chat with History](#voice-chat-with-history)
3. [Language Support](#language-support)
4. [Error Handling](#error-handling)
5. [Best Practices](#best-practices)

---

## Chat History API

The chatbot supports loading conversation history from past conversations. You can choose to load:
- **No history** (default): Only uses current conversation context
- **3 days**: Last 3 days of conversations
- **7 days**: Last 7 days of conversations
- **All history**: All available conversation history

### Endpoints

- `POST /chat` - JSON response
- `POST /chat/html` - HTML response

### Request Format

```json
{
  "message": "Your question here",
  "user_id": "user123",
  "conversation_id": "optional-conversation-id",
  "history_days": 3  // Optional: 3, 7, -1, or omit for no history
}
```

---

### No History (Default)

When no history option is selected, omit `history_days` or set it to `null`. The API will only use the current conversation's context.

**Example Request:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What are some healthy breakfast options?",
    "user_id": "demo_user_001",
    "conversation_id": "current-conv-123"
  }'
```

**Or with explicit null:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What are some healthy breakfast options?",
    "user_id": "demo_user_001",
    "conversation_id": "current-conv-123",
    "history_days": null
  }'
```

**Response:**

```json
{
  "answer": "Here are some healthy breakfast options: Oatmeal with fruits and nuts, Greek yogurt with berries, whole grain toast with avocado...",
  "conversation_id": "current-conv-123"
}
```

**What happens:**
- Only uses current conversation context from `conversation_id`
- Does NOT load past conversations from logs
- Uses in-memory conversation history
- Most efficient option (no file I/O)

---

### 3 Days History

Load conversations from the last 3 days and merge with current conversation context.

**Example Request:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What recipes did we discuss recently?",
    "user_id": "demo_user_001",
    "conversation_id": "current-conv-123",
    "history_days": 3
  }'
```

**Response:**

```json
{
  "answer": "Based on our recent conversations over the last 3 days, we discussed several recipes including: Grilled salmon with vegetables, Chicken stir-fry, and Mediterranean quinoa salad...",
  "conversation_id": "current-conv-123"
}
```

**What happens:**
- Loads all conversations from the last 3 days for the specified `user_id`
- Merges them with current conversation context
- Chatbot can reference those recent conversations
- Useful for continuing recent discussions

---

### 7 Days History

Load conversations from the last 7 days and merge with current conversation context.

**Example Request:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What meals have we planned this week?",
    "user_id": "demo_user_001",
    "conversation_id": "current-conv-123",
    "history_days": 7
  }'
```

**Response:**

```json
{
  "answer": "Looking at our conversations from the past week, we've planned several meals: Monday - Grilled chicken with roasted vegetables, Tuesday - Pasta with marinara sauce, Wednesday - Salmon with quinoa...",
  "conversation_id": "current-conv-123"
}
```

**What happens:**
- Loads all conversations from the last 7 days
- Provides broader context for weekly meal planning
- Useful for meal planning and weekly reviews

---

### All History

Load ALL available conversation history (up to 1 year, max 1000 conversations).

**Example Request:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What have we discussed in all our conversations?",
    "user_id": "demo_user_001",
    "conversation_id": "current-conv-123",
    "history_days": -1
  }'
```

**Response:**

```json
{
  "answer": "Throughout our conversations, we've covered a wide range of topics: breakfast options (oatmeal, yogurt, smoothies), dinner recipes (grilled salmon, chicken stir-fry, pasta dishes), meal planning strategies, nutritional information, calorie tracking, and dietary preferences...",
  "conversation_id": "current-conv-123"
}
```

**What happens:**
- Loads ALL available conversation history for the user
- Searches through all log files (up to 1 year)
- Provides complete context of all past conversations
- Maximum limit: 1000 conversations (to prevent overwhelming the context)
- May take longer to process if there are many conversations

---

## Voice Chat API

The voice chat feature allows users to send audio messages and receive audio responses. It supports both Arabic and English, automatically detecting the language and responding in the same language.

### Endpoints

- `POST /chat/voice` - Voice input → Voice output (returns audio + text)
- `POST /chat/voice/text` - Voice input → Text output (for debugging/preview)

### Supported Audio Formats

- WebM (recommended for web browsers)
- MP3
- WAV
- M4A
- OGG

### Maximum File Size

- Default: 25MB (configurable via `FOOD_BOT_MAX_AUDIO_SIZE_MB`)

---

### Voice Input → Voice Output

Send an audio file and receive an audio response with transcript and text.

**Example Request:**

```bash
curl -X POST "http://localhost:8000/chat/voice" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "audio=@/path/to/your/audio.webm" \
  -F "user_id=demo_user_001" \
  -F "conversation_id=voice-conv-123"
```

**Or with history:**

```bash
curl -X POST "http://localhost:8000/chat/voice" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "audio=@/path/to/your/audio.webm" \
  -F "user_id=demo_user_001" \
  -F "conversation_id=voice-conv-123" \
  -F "history_days=7"
```

**Response:**

```json
{
  "transcript": "What are some healthy breakfast options?",
  "answer_text": "Here are some healthy breakfast options: Oatmeal with fruits and nuts, Greek yogurt with berries, whole grain toast with avocado...",
  "conversation_id": "voice-conv-123",
  "detected_language": "en",
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA..."
}
```

**Response Fields:**
- `transcript`: What the user said (transcribed from audio)
- `answer_text`: Text version of the chatbot's response
- `conversation_id`: Conversation identifier for context
- `detected_language`: Language code ("ar" for Arabic, "en" for English)
- `audio_base64`: Base64-encoded MP3 audio response (can be decoded and played)

**Using the Audio Response:**

```javascript
// JavaScript example
const response = await fetch('/chat/voice', { ... });
const data = await response.json();

// Decode base64 audio
const audioBytes = atob(data.audio_base64);
const audioBlob = new Blob([new Uint8Array(audioBytes.length).map((_, i) => audioBytes.charCodeAt(i))], {
  type: 'audio/mpeg'
});

// Create audio element and play
const audioUrl = URL.createObjectURL(audioBlob);
const audio = new Audio(audioUrl);
audio.play();
```

---

### Voice Input → Text Output

Send an audio file and receive only text response (useful for debugging or preview).

**Example Request:**

```bash
curl -X POST "http://localhost:8000/chat/voice/text" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "audio=@/path/to/your/audio.webm" \
  -F "user_id=demo_user_001" \
  -F "conversation_id=voice-conv-123"
```

**Response:**

```json
{
  "transcript": "ما هي أفضل طريقة لتحضير الكبسة؟",
  "answer_text": "لتحضير الكبسة، ابدأ بتسخين الزيت في قدر كبير. أضف البصل المفروم وقلبه حتى يصبح ذهبياً...",
  "conversation_id": "voice-conv-123",
  "detected_language": "ar",
  "audio_base64": null
}
```

**Note:** `audio_base64` is `null` for this endpoint since it only returns text.

---

### Voice Chat with History

You can combine voice chat with history loading to provide context from past conversations.

**Example: Voice chat with 7 days history**

```bash
curl -X POST "http://localhost:8000/chat/voice" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "audio=@/path/to/your/audio.webm" \
  -F "user_id=demo_user_001" \
  -F "conversation_id=voice-conv-123" \
  -F "history_days=7"
```

**What happens:**
1. Audio is transcribed to text
2. Language is detected (Arabic or English)
3. Past 7 days of conversations are loaded from logs
4. Chatbot processes the question with full context
5. Response is generated in the same language as input
6. Response is converted to audio (matching the input language)

---

## Language Support

### Automatic Language Detection

The voice chat API automatically detects the language from the audio input:
- **Arabic audio** → Detected as "ar" → Response in Arabic → Arabic audio output
- **English audio** → Detected as "en" → Response in English → English audio output

### Text Chat Language Support

The text chat endpoints (`/chat`, `/chat/html`) also support Arabic:
- If the question contains Arabic characters, the chatbot responds in Arabic
- If the question is in English, the chatbot responds in English

**Example: Arabic Text Chat**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "ما هي أفضل طريقة لتحضير الكبسة؟",
    "user_id": "demo_user_001"
  }'
```

**Response (in Arabic):**

```json
{
  "answer": "لتحضير الكبسة، ابدأ بتسخين الزيت في قدر كبير. أضف البصل المفروم وقلبه حتى يصبح ذهبياً...",
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## Error Handling

### Invalid History Days

If an invalid `history_days` value is provided:

**Request:**
```json
{
  "message": "Hello",
  "user_id": "demo_user_001",
  "history_days": 5
}
```

**Response:**
```json
{
  "detail": "history_days must be 3 (last 3 days), 7 (last 7 days), or -1 (all history)"
}
```

**Status Code:** `400 Bad Request`

---

### Unsupported Audio Format

If an unsupported audio format is uploaded:

**Response:**
```json
{
  "detail": "Unsupported audio format. Supported formats: WebM, MP3, WAV, M4A, OGG"
}
```

**Status Code:** `400 Bad Request`

---

### Audio File Too Large

If the audio file exceeds the maximum size:

**Response:**
```json
{
  "detail": "Audio file too large. Maximum size: 25MB"
}
```

**Status Code:** `400 Bad Request`

---

### Speech-to-Text Failure

If the audio cannot be transcribed:

**Response:**
```json
{
  "detail": "Could not transcribe audio. Please ensure audio contains clear speech."
}
```

**Status Code:** `400 Bad Request`

---

### Text-to-Speech Failure

If TTS conversion fails, the API still returns the text response but `audio_base64` will be `null`:

**Response:**
```json
{
  "transcript": "What are some healthy breakfast options?",
  "answer_text": "Here are some healthy breakfast options...",
  "conversation_id": "voice-conv-123",
  "detected_language": "en",
  "audio_base64": null
}
```

**Status Code:** `200 OK` (with warning logged)

---

## Best Practices

### 1. Conversation ID Management

- **Always use `conversation_id`** to maintain context across multiple messages
- Store the `conversation_id` from the response and reuse it in subsequent requests
- Generate a new `conversation_id` for new conversation sessions

**Example Flow:**

```javascript
// First message
const response1 = await fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'YOUR_API_KEY'
  },
  body: JSON.stringify({
    message: "What are healthy breakfast options?",
    user_id: "user123"
  })
});
const data1 = await response1.json();
const conversationId = data1.conversation_id; // Store this!

// Follow-up message (uses same conversation_id)
const response2 = await fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'YOUR_API_KEY'
  },
  body: JSON.stringify({
    message: "Tell me more about oatmeal",
    user_id: "user123",
    conversation_id: conversationId // Reuse the conversation_id
  })
});
```

---

### 2. History Loading Strategy

- **No history**: Use for new conversations or when you only need current session context
- **3 days**: Use for recent meal planning or quick follow-ups
- **7 days**: Use for weekly meal planning and reviews
- **All history**: Use sparingly, only when you need comprehensive context (may be slower)

**When to use each:**
- **No history**: Default for most conversations
- **3 days**: "What did we discuss recently?"
- **7 days**: "What meals did we plan this week?"
- **All history**: "What are my favorite recipes?" or "What dietary preferences have I mentioned?"

---

### 3. Voice Chat Tips

- **Audio Quality**: Ensure clear audio for better transcription
- **File Format**: WebM is recommended for web browsers, MP3 for compatibility
- **File Size**: Keep audio files under 25MB (shorter messages are better)
- **Language**: Speak clearly in either Arabic or English
- **Testing**: Use `/chat/voice/text` endpoint first to verify transcription before using full voice endpoint

---

### 4. Error Handling

Always handle potential errors:

```javascript
try {
  const response = await fetch('/chat/voice', {
    method: 'POST',
    headers: { 'X-API-Key': 'YOUR_API_KEY' },
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error.detail);
    // Handle error (show user-friendly message)
    return;
  }
  
  const data = await response.json();
  // Process successful response
} catch (error) {
  console.error('Network Error:', error);
  // Handle network error
}
```

---

### 5. User Experience

- **Show loading states** when processing voice or loading history
- **Display transcript** so users can verify what was understood
- **Provide text fallback** if audio response fails
- **Cache conversation_id** in browser storage for session persistence
- **Handle language switching** gracefully (Arabic ↔ English)

---

## Complete Example: Voice Chat with History

Here's a complete example combining voice chat with 7-day history:

**Request:**

```bash
curl -X POST "http://localhost:8000/chat/voice" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "audio=@question_about_recent_meals.webm" \
  -F "user_id=demo_user_001" \
  -F "conversation_id=weekly-meal-plan-123" \
  -F "history_days=7"
```

**Response:**

```json
{
  "transcript": "What meals did we plan this week?",
  "answer_text": "Based on our conversations over the past week, we planned several meals: Monday - Grilled chicken with roasted vegetables, Tuesday - Pasta with marinara sauce, Wednesday - Salmon with quinoa and steamed broccoli...",
  "conversation_id": "weekly-meal-plan-123",
  "detected_language": "en",
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA..."
}
```

**What happened:**
1. ✅ Audio file uploaded and validated
2. ✅ Speech-to-text conversion (detected English)
3. ✅ Loaded 7 days of conversation history
4. ✅ Processed question with full context
5. ✅ Generated response in English
6. ✅ Converted response to English audio
7. ✅ Returned audio + text response

---

## API Authentication

All endpoints require API key authentication via the `X-API-Key` header:

```bash
-H "X-API-Key: YOUR_API_KEY"
```

Get your API key from the `.env` file or your administrator.

---

## Support

For issues or questions:
- Check the error messages for specific guidance
- Verify your API key is correct
- Ensure audio files are in supported formats
- Confirm `user_id` is provided when using history features

---

**Last Updated:** December 2024

