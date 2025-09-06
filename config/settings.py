import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
TTS_ENGINE = 'pyttsx3'
DB_PATH = os.path.join(BASE_DIR, 'knowledge.db')
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
DEFAULT_AGENT_NAME = 'DefaultAgent'
DEFAULT_SYSTEM_PROMPT = """
Eres un asistente útil. Sigue las reglas del agente especificadas en la base de datos.
"""
DEFAULT_BACKEND = 'ollama'
DEFAULT_MODEL = 'phi3:mini'
DEFAULT_MAX_WORDS_RESPONSE =1000
DEFAULT_LANGUAGE = 'es-MX'
DEFAULT_EXTRA_DATA = '{"tts_backend": "web_speech", "tts_language": "es-MX", "tts_voice": "male", "tts_api_key": ""}'