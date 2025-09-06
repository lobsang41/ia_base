import os
import sys
import base64

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from modules.tts_stt.tts import TTS

# Test ElevenLabs audio generation
tts = TTS(
    tts_backend='elevenlabs',
    tts_language='es-MX',
    tts_voice='Rachel',
    tts_api_key='sk_c32b564b48f88160efb46ae678ff537d2506319e1a42a13e',
    agent_name='FoodAgent'
)
audio_data = tts.speak("Prueba de audio para tacos al pastor")
if audio_data and audio_data.get('audio'):
    print("Audio data generated successfully")
    # Save audio to file for testing
    with open("test.mp3", "wb") as f:
        f.write(base64.b64decode(audio_data['audio']))
else:
    print("Failed to generate audio data:", audio_data)