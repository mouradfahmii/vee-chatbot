# Vee Food & Recipes Chatbot

End-to-end chatbot prototype for culinary coaching apps. It loads synthetic
knowledge (users, sessions, meals, insights) into ChromaDB, exposes a
retrieval-augmented chat pipeline, and ships both CLI + FastAPI interfaces.

## Stack
- Python 3.11+
- ChromaDB with sentence-transformer embeddings
- LiteLLM-compatible LLM calls (OpenAI, Azure, local, etc.)
- FastAPI + Uvicorn for HTTP access

## Project Layout
```
data/                           Synthetic JSON knowledge base
app/config.py                   Central settings
app/ingest.py                   JSON -> Chroma embedding pipeline
app/vector_store.py             Chroma wrapper
app/prompts.py                  System + chat templates
app/chatbot.py                  Retrieval + prompting orchestration
app/llm.py                      LiteLLM wrapper
app/logger.py                   Conversation logging utility
api/main.py                     FastAPI application
api/schemas.py                  Request/response types
scripts/seed_chroma.py          Seeds/refreshes the vector store
scripts/dev_chat.py             Local REPL for quick testing
scripts/quick_test.py            Quick scope handling tests
scripts/test_chatbot.py          Comprehensive conversation simulations
scripts/view_logs.py             View conversation logs
scripts/generate_test_meal.py   Generate test meal image
scripts/test_image_analysis.py   Test image analysis functionality
```

## Getting Started
1. **Install dependencies**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set LLM credentials**
   - Export standard LiteLLM env vars (e.g. `export OPENAI_API_KEY=...`),
     or create `.env` with `FOOD_BOT_LLM_API_KEY` to override.

3. **Seed the vector store**
   ```bash
   python scripts/seed_chroma.py
   ```

4. **Run the API**
   ```bash
   uvicorn api.main:app --reload
   ```
   - `POST /chat` with payload `{ "message": "How do I prep dinner?", "user_id": "U001" }`
     - `user_id` is optional but recommended for user tracking
     - **Requires API key authentication** (see API Authentication section below)
   - `POST /ingest` to rebuild the knowledge base (pass `reset=false` to append)
     - **Requires API key authentication** (admin endpoint)

5. **CLI testing**
   ```bash
   python scripts/dev_chat.py
   ```

6. **Test scope handling**
   ```bash
   PYTHONPATH=. python scripts/quick_test.py
   ```
   The chatbot is configured to decline non-food questions and redirect users to food-related topics.

## Customizing
- Update `data/synthetic_food_chatbot_data.json` with real content.
- Tune retrieval count, embedding model, or prompt text via `app/config.py`.
- Swap the LLM provider by changing `FOOD_BOT_LLM_MODEL` or pointing
  `FOOD_BOT_LLM_API_BASE` at a local endpoint supported by LiteLLM.

## Features
- **Scope Enforcement**: The chatbot automatically declines non-food questions and redirects to culinary topics
- **Retrieval-Augmented**: Answers are grounded in the synthetic knowledge base (meals, sessions, plans)
- **Conversation History**: Supports multi-turn conversations with context awareness
- **Conversation Logging**: All conversations are automatically logged to `logs/` directory
- **Image Analysis**: Analyze food images to identify meals, estimate calories, and identify ingredients

## Logging

The chatbot automatically logs all conversations to the `logs/` directory:

- **`logs/conversations_YYYY-MM-DD.jsonl`**: JSONL file with detailed conversation logs (one per day)
  - Each line contains: timestamp, user_id (optional), question, answer, scope detection, retrieved docs count, history length, and metadata
- **`logs/app.log`**: Standard Python logging output with summary information

Example log entry:
```json
{
  "timestamp": "2025-11-25T10:47:52.841831",
  "user_id": "U001",
  "question": "What's a quick dinner recipe?",
  "answer": "For a quick dinner, I recommend...",
  "is_food_related": true,
  "num_retrieved_docs": 6,
  "history_length": 0,
  "metadata": {
    "model": "openai/gpt-4o-mini",
    "temperature": 0.2
  }
}
```

**Note**: `user_id` is optional. If not provided, it will be `null` in the log entry.

Logs are automatically created when the chatbot processes any question. The `logs/` directory is excluded from git via `.gitignore`.

To view logs:
```bash
PYTHONPATH=. python scripts/view_logs.py [date] [limit]
# Examples:
# python scripts/view_logs.py          # Today's logs, last 10
# python scripts/view_logs.py 5        # Today's logs, last 5
# python scripts/view_logs.py 2025-11-25 20  # Specific date, last 20
```

### AWS S3 Logging

The chatbot can optionally store logs in AWS S3 for long-term storage and analysis. Logs are still written locally, and also uploaded to S3 if configured.

**Setup:**

1. **Install boto3** (if not already installed):
   ```bash
   pip install boto3
   ```

2. **Configure AWS credentials** (one of these methods):
   - Set environment variables: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
   - Use AWS IAM roles (if running on EC2/ECS/Lambda)
   - Use `~/.aws/credentials` file
   - Use AWS SSO

3. **Set environment variables**:
   ```bash
   export AWS_S3_LOG_BUCKET="your-bucket-name"
   export AWS_S3_LOG_PREFIX="vee-chatbot/logs/"  # Optional, defaults to "vee-chatbot/logs/"
   export AWS_REGION="us-east-1"  # Optional, defaults to "us-east-1"
   ```

   Or add to your `.env` file:
   ```
   AWS_S3_LOG_BUCKET=your-bucket-name
   AWS_S3_LOG_PREFIX=vee-chatbot/logs/
   AWS_REGION=us-east-1
   ```

4. **Create S3 bucket** (if it doesn't exist):
   ```bash
   aws s3 mb s3://your-bucket-name --region us-east-1
   ```

**How it works:**
- Logs are written to local `logs/` directory as before (one JSONL file per day for local storage)
- Each conversation is uploaded to S3 as a separate JSON file: `s3://{bucket}/{prefix}/conversations/YYYY-MM-DD/conversation_TIMESTAMP_USERID_UUID.json`
- Multiple conversations per day result in multiple files in S3 (organized by date folder)
- If S3 upload fails, the application continues normally (errors are logged but don't break the app)
- Each conversation file contains the full conversation details as a single JSON object

**S3 IAM Policy Example:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/vee-chatbot/logs/conversations/*"
    }
  ]
}
```

**S3 File Structure:**
```
s3://your-bucket-name/vee-chatbot/logs/
└── conversations/
    ├── 2025-12-06/
    │   ├── conversation_2025-12-06T10-30-15_user123_abc12345.json
    │   ├── conversation_2025-12-06T10-35-22_user456_def67890.json
    │   └── conversation_2025-12-06T11-20-10_user123_ghi11111.json
    └── 2025-12-07/
        └── conversation_2025-12-07T09-15-30_user789_jkl22222.json
```

**Note:** If `AWS_S3_LOG_BUCKET` is not set, logs are only stored locally. The application works fine without AWS configuration.

## API Authentication

The API is secured with API key authentication. All endpoints require a valid API key in the request header.

### Setup

1. **API key is already generated** and stored in your `.env` file:
   ```
   API_KEY=2fdbDpPU4JfwOGAlDqKJjdifDXVy3NBNPyXa1iRnOsI
   ```

2. **Generate a new key** (if needed):
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

### Usage

**All API requests must include the `X-API-Key` header:**

```bash
# Using curl
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 2fdbDpPU4JfwOGAlDqKJjdifDXVy3NBNPyXa1iRnOsI" \
  -d '{"message": "What is a quick meal?", "user_id": "U001"}'
```

**Python example:**
```python
import requests

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "2fdbDpPU4JfwOGAlDqKJjdifDXVy3NBNPyXa1iRnOsI"
}

response = requests.post(
    "http://localhost:8000/chat",
    headers=headers,
    json={"message": "What is a quick meal?", "user_id": "U001"}
)
print(response.json())
```

**JavaScript example:**
```javascript
fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': '2fdbDpPU4JfwOGAlDqKJjdifDXVy3NBNPyXa1iRnOsI'
  },
  body: JSON.stringify({
    message: 'What is a quick meal?',
    user_id: 'U001'
  })
})
```

### Testing Authentication

Run the test script to verify authentication works:
```bash
# Make sure the API is running first
uvicorn api.main:app --reload

# In another terminal, run the test
PYTHONPATH=. python scripts/test_api_auth.py
```

### Security Notes

- **Keep your API key secret** - don't commit it to git (`.env` is already in `.gitignore`)
- **Use HTTPS in production** - never send API keys over unencrypted connections
- **One key for everything** - same key works for local testing and production
- **If key is leaked** - generate a new one and update both server and clients

### Development Mode

If `API_KEY` is not set in `.env`, the API will allow all requests (useful for local development without authentication). **Always set an API key in production!**

## Image Analysis

The chatbot can analyze food images to:
- Identify meals and dishes
- Estimate calories
- List ingredients
- Provide nutritional insights

### API Usage

**Upload an image for analysis:**
```bash
curl -X POST "http://localhost:8000/chat/image" \
  -H "X-API-Key: 2fdbDpPU4JfwOGAlDqKJjdifDXVy3NBNPyXa1iRnOsI" \
  -F "image=@path/to/meal.jpg" \
  -F "question=How many calories are in this meal?" \
  -F "user_id=U001"
```

**Python usage:**
```python
from app.chatbot import bot

# Analyze image
answer = bot.answer_with_image(
    "path/to/meal.jpg",
    question="How many calories are in this meal?",
    user_id="U001"
)
```

### Image Validation

The chatbot automatically validates that uploaded images contain food-related content. Non-food images are rejected with a polite message redirecting users to upload food images.

### Testing Image Analysis

1. **Generate a test meal image:**
   ```bash
   PYTHONPATH=. python scripts/generate_test_meal.py
   ```

2. **Test image analysis:**
   ```bash
   PYTHONPATH=. python scripts/test_image_analysis.py
   ```

### Vision Model Configuration

The vision model can be configured via environment variable:
```bash
export FOOD_BOT_VISION_MODEL="openai/gpt-4o"  # Default
# or
export FOOD_BOT_VISION_MODEL="openai/gpt-4o-mini"  # Also supports vision
```

## Next Steps
- Add auth + user scoping around session history.
- Stream responses over Server-Sent Events for realtime UIs.
- Plug in actual calorie-computer microservices when available.
