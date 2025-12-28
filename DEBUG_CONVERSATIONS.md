# Debugging Conversations API - Server Issues

## Problem: `/conversations` returns 200 but empty list

### Common Causes:

1. **User ID Mismatch**
   - The `user_id` you use in `/conversations?user_id=XXX` must **exactly match** the `user_id` you used when chatting
   - Check: Did you include `user_id` in your chat requests?
   - Check: Is the `user_id` the same in both calls?

2. **Logs Not Written Yet**
   - Logs are written to `logs/conversations_YYYY-MM-DD.jsonl` (UTC date)
   - The file is created when the first conversation is logged
   - Check: Does the log file exist on the server?

3. **Timezone Issue**
   - Log files use UTC date (`datetime.utcnow()`)
   - If server timezone is different, the file might be named for a different date
   - Check: What date is the log file? (should match UTC date, not local server time)

### Quick Debug Steps:

1. **Check if logs are being written:**
   ```bash
   # On server, check if log files exist
   ls -la logs/conversations_*.jsonl
   
   # Check today's log (UTC date)
   cat logs/conversations_$(date -u +%Y-%m-%d).jsonl | tail -5
   ```

2. **Verify user_id in logs:**
   ```bash
   # Check what user_ids are in today's log
   cat logs/conversations_$(date -u +%Y-%m-%d).jsonl | jq -r '.user_id' | sort | uniq
   ```

3. **Test with a known user_id:**
   - Use one of the user_ids from the logs
   - Example: If logs show `user_id: "demo_user_001"`, use that in your API call

4. **Check API request:**
   ```bash
   # Make sure you're using the exact same user_id
   curl -X GET "http://your-server:8000/conversations?user_id=EXACT_USER_ID" \
     -H "X-API-Key: YOUR_API_KEY"
   ```

### Test Script:

Run this on your server (update BASE_URL and API_KEY):

```bash
python scripts/test_conversations_api.py
```

This will:
1. Create a test conversation with a known user_id
2. List conversations for that user_id
3. Get the conversation detail
4. Show you exactly what's happening

### Manual Check:

1. **Make a chat request with user_id:**
   ```bash
   curl -X POST "http://your-server:8000/chat" \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What are healthy breakfast options?",
       "user_id": "test_user_001"
     }'
   ```

2. **Note the conversation_id from response**

3. **List conversations:**
   ```bash
   curl -X GET "http://your-server:8000/conversations?user_id=test_user_001" \
     -H "X-API-Key: YOUR_API_KEY"
   ```
   
   **Important:** Use the EXACT same `user_id` as in step 1!

4. **Check server logs:**
   ```bash
   # Find the log file (UTC date)
   UTC_DATE=$(date -u +%Y-%m-%d)
   cat logs/conversations_${UTC_DATE}.jsonl | jq '.user_id, .conversation_id' | tail -10
   ```

### If Still Not Working:

Check the `list_user_conversations` method in `app/logger.py`:
- It searches up to 365 days back
- It filters by `entry_user_id == user_id` (exact match, case-sensitive)
- It requires both `user_id` and `conversation_id` to be present

**Debug output:**
Add temporary logging in `app/logger.py` line ~318:
```python
if entry_user_id == user_id and entry_conversation_id:
    print(f"DEBUG: Found match - user_id={entry_user_id}, conv_id={entry_conversation_id}")
```

