#!/usr/bin/env python3
"""
Test voice chat endpoint with the same request format as the Flutter app.
"""

import os
import requests
import wave
import struct
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "http://127.0.0.1:8001"
API_KEY = os.getenv("API_KEY") or os.getenv("VEE_CHATBOT_API_KEY")

def create_test_wav_file(filename: str = "test_audio.wav", duration_seconds: float = 1.0):
    """Create a simple test WAV file."""
    import math
    
    sample_rate = 16000
    num_samples = int(sample_rate * duration_seconds)
    
    # Create a simple sine wave tone
    frequency = 440  # A4 note
    amplitude = 0.3  # Volume (30%)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = []
        for i in range(num_samples):
            # Generate sine wave: sin(2π * frequency * time)
            time = i / sample_rate
            value = int(32767 * amplitude * math.sin(2 * math.pi * frequency * time))
            # Clamp to valid range
            value = max(-32768, min(32767, value))
            frames.append(struct.pack('<h', value))
        
        wav_file.writeframes(b''.join(frames))
    
    return filename

def test_voice_endpoint():
    """Test the voice chat endpoint with the same format as Flutter request."""
    print("=" * 60)
    print("Testing Voice Chat Endpoint")
    print("=" * 60)
    
    # Create a test audio file
    audio_file = create_test_wav_file()
    print(f"\n✓ Created test audio file: {audio_file}")
    
    # Prepare the request exactly as Flutter sends it
    url = f"{API_BASE_URL}/chat/voice"
    headers = {
        "X-API-Key": API_KEY,
        "Accept": "application/json"
    }
    
    # Form data matching the Flutter request
    form_data = {
        "user_id": "bf75e372-5049-421b-8e9f-a714649e770c",
        "conversation_id": "",  # Empty string as in Flutter request
        "history_days": "-1"  # String as in Flutter request
    }
    
    # File upload
    files = {
        "audio": ("audio_1769365208820.wav", open(audio_file, "rb"), "audio/x-wav")
    }
    
    print(f"\nSending request to: {url}")
    print(f"Headers: X-API-Key present: {bool(API_KEY)}")
    print(f"Form data:")
    for key, value in form_data.items():
        print(f"  {key}: {value}")
    print(f"Audio file: {audio_file} (audio/x-wav)")
    
    try:
        response = requests.post(url, files=files, data=form_data, headers=headers)
        files["audio"][1].close()  # Close the file
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ SUCCESS!")
            print(f"  Status: {data.get('status')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Conversation ID: {data.get('conversation_id')}")
            print(f"  Detected Language: {data.get('detected_language')}")
            print(f"  Transcript: {data.get('transcript', '')[:100]}...")
            print(f"  Response (first 200 chars): {data.get('data', '')[:200]}...")
            if data.get('audio_base64'):
                print(f"  Audio Response: Present ({len(data.get('audio_base64', ''))} chars base64)")
            else:
                print(f"  Audio Response: Not present")
            return True
        else:
            print(f"\n✗ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error details: {error_data}")
            except:
                print(f"  Response text: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n✗ EXCEPTION: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test file
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"\n✓ Cleaned up test file: {audio_file}")

if __name__ == "__main__":
    test_voice_endpoint()
