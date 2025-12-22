# API Examples: History Loading Options

## Overview

The chatbot supports three history loading options:
- **3 days**: Load conversations from the last 3 days
- **7 days**: Load conversations from the last 7 days  
- **All history**: Load all available conversation history (`history_days: -1`)

## API Endpoint

**POST** `/chat` or `/chat/html`

## Request Format

```json
{
  "message": "Your question here",
  "user_id": "user123",
  "history_days": 3  // or 7, or -1 for all history
}
```

---

## Example 1: Load Last 3 Days History

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What recipes did we discuss recently?",
    "user_id": "demo_user_001",
    "history_days": 3
  }'
```

**Response:**
```json
{
  "answer": "Based on our recent conversations, we discussed...",
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**What happens:**
- Loads all conversations from the last 3 days for `demo_user_001`
- Merges them with current conversation context
- Chatbot can reference those recent conversations

---

## Example 2: Load Last 7 Days History

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What did we talk about this week?",
    "user_id": "demo_user_001",
    "history_days": 7
  }'
```

**Response:**
```json
{
  "answer": "This week we discussed breakfast options including oatmeal, dinner recipes like grilled salmon, and meal planning...",
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**What happens:**
- Loads all conversations from the last 7 days for `demo_user_001`
- Provides broader context of the week's discussions
- Chatbot can reference conversations from the entire week

---

## Example 3: Load All History

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What have we discussed in all our conversations?",
    "user_id": "demo_user_001",
    "history_days": -1
  }'
```

**Response:**
```json
{
  "answer": "Throughout our conversations, we've covered breakfast options (oatmeal, yogurt), dinner recipes (grilled salmon, chicken stir-fry), meal planning, and nutritional information...",
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**What happens:**
- Loads ALL available conversation history for `demo_user_001`
- Searches through all log files (up to 1 year)
- Provides complete context of all past conversations
- Maximum limit: 1000 conversations (to prevent overwhelming the context)

---

## HTML Endpoint Examples

### Example 1: 3 Days History (HTML)

```bash
curl -X POST "http://localhost:8000/chat/html" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "ما هي الوصفات التي ناقشناها؟",
    "user_id": "demo_user_001",
    "history_days": 3
  }'
```

**Response:** HTML formatted response with Arabic content

---

### Example 2: 7 Days History (HTML)

```bash
curl -X POST "http://localhost:8000/chat/html" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "What recipes did we discuss this week?",
    "user_id": "demo_user_001",
    "history_days": 7
  }'
```

**Response:** HTML formatted response

---

### Example 3: All History (HTML)

```bash
curl -X POST "http://localhost:8000/chat/html" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "message": "Summarize everything we've discussed",
    "user_id": "demo_user_001",
    "history_days": -1
  }'
```

**Response:** HTML formatted response with complete history summary

---

## Frontend Integration

### JavaScript Example

```javascript
// Option 1: Load 3 days history
async function chatWithHistory3Days(message, userId) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'YOUR_API_KEY'
    },
    body: JSON.stringify({
      message: message,
      user_id: userId,
      history_days: 3
    })
  });
  return await response.json();
}

// Option 2: Load 7 days history
async function chatWithHistory7Days(message, userId) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'YOUR_API_KEY'
    },
    body: JSON.stringify({
      message: message,
      user_id: userId,
      history_days: 7
    })
  });
  return await response.json();
}

// Option 3: Load all history
async function chatWithAllHistory(message, userId) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'YOUR_API_KEY'
    },
    body: JSON.stringify({
      message: message,
      user_id: userId,
      history_days: -1
    })
  });
  return await response.json();
}
```

### React Example

```jsx
function ChatComponent() {
  const [historyOption, setHistoryOption] = useState(null); // 3, 7, or -1
  
  const sendMessage = async (message) => {
    const payload = {
      message: message,
      user_id: "user123"
    };
    
    if (historyOption) {
      payload.history_days = historyOption;
    }
    
    const response = await fetch('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'YOUR_API_KEY'
      },
      body: JSON.stringify(payload)
    });
    
    return await response.json();
  };
  
  return (
    <div>
      <button onClick={() => setHistoryOption(3)}>Load 3 Days</button>
      <button onClick={() => setHistoryOption(7)}>Load 7 Days</button>
      <button onClick={() => setHistoryOption(-1)}>Load All History</button>
      {/* Chat interface */}
    </div>
  );
}
```

---

## Notes

- **`user_id` is required** when using `history_days` - history is filtered by user
- **`history_days` values**: Only `3`, `7`, or `-1` are accepted
- **All history limit**: Maximum 1000 conversations to prevent context overflow
- **Performance**: All history may take longer to load if there are many conversations
- **Conversation ID**: You can still use `conversation_id` along with `history_days` - both will be merged

---

## Error Handling

If invalid `history_days` value is provided:

```json
{
  "detail": "history_days must be 3 (last 3 days), 7 (last 7 days), or -1 (all history)"
}
```

Status Code: `400 Bad Request`

