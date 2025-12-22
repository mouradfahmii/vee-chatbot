"""
Test script for voice chat endpoints.
Simulates voice conversations and verifies logging.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logger import conversation_logger


def simulate_voice_conversations():
    """Simulate voice conversations for testing."""
    
    # Test user IDs
    test_user_1 = "test_user_voice_001"
    test_user_2 = "test_user_voice_002"
    
    # Simulate conversations over the last 7 days
    base_date = datetime.utcnow()
    
    print("=" * 80)
    print("Simulating Voice Conversations")
    print("=" * 80)
    print()
    
    # Day 7: Arabic voice conversation
    day_7 = base_date - timedelta(days=7)
    conversation_id_1 = "voice-conv-arabic-001"
    
    print(f"Day 7 ({day_7.strftime('%Y-%m-%d')}): Arabic Voice Conversation")
    print(f"  Conversation ID: {conversation_id_1}")
    print(f"  User ID: {test_user_1}")
    print()
    
    # Simulate Arabic voice input
    arabic_questions = [
        "ما هي أفضل طريقة لتحضير الكبسة؟",
        "كم عدد السعرات الحرارية في صحن من الكبسة؟",
        "ما هي المكونات الأساسية للكبسة؟"
    ]
    
    arabic_answers = [
        "لتحضير الكبسة، ابدأ بتسخين الزيت في قدر كبير. أضف البصل المفروم وقلبه حتى يصبح ذهبياً. ثم أضف اللحم أو الدجاج وقلبه حتى ينضج. أضف التوابل مثل الهيل والقرنفل والقرفة. ثم أضف الأرز والماء واتركه يغلي. بعد ذلك، غط القدر واتركه على نار هادئة لمدة 20-30 دقيقة حتى ينضج الأرز.",
        "صحن من الكبسة (حوالي 300 جرام) يحتوي على حوالي 450-550 سعرة حرارية، اعتماداً على كمية اللحم أو الدجاج والزيت المستخدم.",
        "المكونات الأساسية للكبسة تشمل: الأرز البسمتي، اللحم أو الدجاج، البصل، الثوم، التوابل (هيل، قرنفل، قرفة، فلفل أسود)، الزيت أو السمن، والماء أو المرق."
    ]
    
    for i, (question, answer) in enumerate(zip(arabic_questions, arabic_answers)):
        # Log with timestamp from day 7
        timestamp = (day_7 + timedelta(hours=i+1)).isoformat()
        
        conversation_logger.log_conversation(
            question=question,
            answer=answer,
            is_food_related=True,
            num_retrieved_docs=2,
            history_length=i,
            user_id=test_user_1,
            conversation_id=conversation_id_1,
            metadata={
                "model": "openai/gpt-4o-mini",
                "temperature": 0.5,
                "voice_input": True,
                "detected_language": "ar",
                "audio_format": "webm",
                "simulated": True,
                "day": 7,
            },
        )
        print(f"  ✓ Logged turn {i+1}: Arabic question about Kabsa")
    
    print()
    
    # Day 5: English voice conversation
    day_5 = base_date - timedelta(days=5)
    conversation_id_2 = "voice-conv-english-001"
    
    print(f"Day 5 ({day_5.strftime('%Y-%m-%d')}): English Voice Conversation")
    print(f"  Conversation ID: {conversation_id_2}")
    print(f"  User ID: {test_user_2}")
    print()
    
    english_questions = [
        "What are some healthy breakfast options?",
        "How many calories are in a bowl of oatmeal?",
        "Can you suggest a low-calorie dinner recipe?"
    ]
    
    english_answers = [
        "Some healthy breakfast options include: oatmeal with fruits and nuts, Greek yogurt with berries, whole grain toast with avocado, scrambled eggs with vegetables, or a smoothie with spinach and protein powder.",
        "A bowl of oatmeal (about 1 cup cooked, made with water) contains approximately 150-200 calories. If you add fruits, nuts, or milk, the calorie count will increase accordingly.",
        "Here's a low-calorie dinner recipe: Grilled chicken breast (150g) with steamed vegetables (broccoli, carrots, green beans) and a small portion of quinoa. This meal is approximately 350-400 calories and provides a good balance of protein, fiber, and nutrients."
    ]
    
    for i, (question, answer) in enumerate(zip(english_questions, english_answers)):
        timestamp = (day_5 + timedelta(hours=i+1)).isoformat()
        
        conversation_logger.log_conversation(
            question=question,
            answer=answer,
            is_food_related=True,
            num_retrieved_docs=3,
            history_length=i,
            user_id=test_user_2,
            conversation_id=conversation_id_2,
            metadata={
                "model": "openai/gpt-4o-mini",
                "temperature": 0.5,
                "voice_input": True,
                "detected_language": "en",
                "audio_format": "mp3",
                "simulated": True,
                "day": 5,
            },
        )
        print(f"  ✓ Logged turn {i+1}: English question about healthy meals")
    
    print()
    
    # Day 3: Mixed language conversation (Arabic then English)
    day_3 = base_date - timedelta(days=3)
    conversation_id_3 = "voice-conv-mixed-001"
    
    print(f"Day 3 ({day_3.strftime('%Y-%m-%d')}): Mixed Language Voice Conversation")
    print(f"  Conversation ID: {conversation_id_3}")
    print(f"  User ID: {test_user_1}")
    print()
    
    mixed_questions = [
        "ما هي أفضل طريقة لتحضير السلطة؟",
        "What is the calorie count for a typical salad?",
    ]
    
    mixed_answers = [
        "لتحضير سلطة صحية، ابدأ باختيار الخضار الطازجة مثل الخس، الطماطم، الخيار، والفلفل. أضف مصدر بروتين مثل الدجاج المشوي أو التونة. استخدم صلصة خفيفة مثل زيت الزيتون والليمون بدلاً من الصلصات الثقيلة.",
        "A typical garden salad (about 200g) with mixed greens, tomatoes, cucumbers, and a light vinaigrette contains approximately 50-100 calories. If you add protein like grilled chicken (100g), it adds about 150-200 calories, bringing the total to around 200-300 calories."
    ]
    
    for i, (question, answer) in enumerate(zip(mixed_questions, mixed_answers)):
        timestamp = (day_3 + timedelta(hours=i+1)).isoformat()
        detected_lang = "ar" if i == 0 else "en"
        
        conversation_logger.log_conversation(
            question=question,
            answer=answer,
            is_food_related=True,
            num_retrieved_docs=2,
            history_length=i,
            user_id=test_user_1,
            conversation_id=conversation_id_3,
            metadata={
                "model": "openai/gpt-4o-mini",
                "temperature": 0.5,
                "voice_input": True,
                "detected_language": detected_lang,
                "audio_format": "webm" if i == 0 else "mp3",
                "simulated": True,
                "day": 3,
            },
        )
        print(f"  ✓ Logged turn {i+1}: {'Arabic' if i == 0 else 'English'} question about salads")
    
    print()
    print("=" * 80)
    print("Voice Conversation Simulation Complete!")
    print("=" * 80)
    print()
    print(f"Generated conversations for:")
    print(f"  - User {test_user_1}: 2 conversations (Arabic, Mixed)")
    print(f"  - User {test_user_2}: 1 conversation (English)")
    print()
    print("You can now test the voice endpoints with these user IDs:")
    print(f"  - {test_user_1} (has 7-day and 3-day history)")
    print(f"  - {test_user_2} (has 5-day history)")
    print()


def display_voice_logs():
    """Display voice conversation logs from the last 7 days."""
    
    print("=" * 80)
    print("Voice Conversation Logs (Last 7 Days)")
    print("=" * 80)
    print()
    
    # Find log files from the last 7 days
    log_dir = Path(__file__).parent.parent / "logs"
    log_files = sorted(log_dir.glob("conversations_*.jsonl"), reverse=True)
    
    if not log_files:
        print("No log files found.")
        return
    
    voice_entries = []
    
    # Read log files from the last 7 days
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    for log_file in log_files:
        # Extract date from filename
        try:
            date_str = log_file.stem.split("_")[1]  # conversations_YYYY-MM-DD.jsonl
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff_date:
                continue
        except (IndexError, ValueError):
            continue
        
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    # Check if it's a voice conversation
                    metadata = entry.get("metadata", {})
                    if metadata.get("voice_input") or metadata.get("detected_language"):
                        voice_entries.append(entry)
                except json.JSONDecodeError:
                    continue
    
    if not voice_entries:
        print("No voice conversation logs found in the last 7 days.")
        return
    
    # Sort by timestamp
    voice_entries.sort(key=lambda x: x.get("timestamp", ""))
    
    print(f"Found {len(voice_entries)} voice conversation entries:")
    print()
    
    for i, entry in enumerate(voice_entries, 1):
        timestamp = entry.get("timestamp", "Unknown")
        user_id = entry.get("user_id", "Unknown")
        conv_id = entry.get("conversation_id", "Unknown")
        question = entry.get("question", "")
        answer = entry.get("answer", "")[:100] + "..." if len(entry.get("answer", "")) > 100 else entry.get("answer", "")
        metadata = entry.get("metadata", {})
        detected_lang = metadata.get("detected_language", "unknown")
        audio_format = metadata.get("audio_format", "unknown")
        
        print(f"Entry {i}:")
        print(f"  Timestamp: {timestamp}")
        print(f"  User ID: {user_id}")
        print(f"  Conversation ID: {conv_id}")
        print(f"  Language: {detected_lang.upper()}")
        print(f"  Audio Format: {audio_format}")
        print(f"  Question: {question[:80]}{'...' if len(question) > 80 else ''}")
        print(f"  Answer: {answer[:80]}{'...' if len(answer) > 80 else ''}")
        print()


if __name__ == "__main__":
    # Configure UTF-8 output for Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    
    # Simulate voice conversations
    simulate_voice_conversations()
    
    # Display logs
    display_voice_logs()

