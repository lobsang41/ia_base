import json
import logging
import os
import base64
from elevenlabs.client import ElevenLabs
import sqlite3
from config.settings import DB_PATH
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)

class TTS:
    def __init__(self, tts_backend='web_speech', tts_language='es-MX', tts_voice='male', tts_api_key='', agent_name=None):
        self.tts_backend = tts_backend
        self.tts_language = tts_language
        self.tts_voice = tts_voice
        self.tts_api_key = tts_api_key or os.getenv('ELEVENLABS_API_KEY', '')
        self.agent_name = agent_name
        self.engine = None
        self.previous_request_ids = []  # For ElevenLabs request stitching (max 3)
        self.text_buffer = []  # Buffer for text chunks
        self.buffer_timeout = 2.0  # Seconds to wait before processing buffer
        self.last_text_time = None

        if not self.tts_api_key and self.agent_name:
            self.load_api_key_from_db()

        logging.info(f'TTS inicializando con backend={self.tts_backend}, api_key={self.tts_api_key}, voice={self.tts_voice}')
        self.init_engine()

    def load_api_key_from_db(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT extra_data FROM agents WHERE name = ?', (self.agent_name,))
            result = cursor.fetchone()
            conn.close()
            if result and result[0]:
                extra_data = json.loads(result[0])
                self.tts_api_key = extra_data.get('tts_api_key', '')
                self.tts_backend = extra_data.get('tts_backend', self.tts_backend)
                self.tts_language = extra_data.get('tts_language', self.tts_language)
                self.tts_voice = extra_data.get('tts_voice', self.tts_voice)
                logging.info(f'Configuración TTS cargada desde la base de datos para agente {self.agent_name}: backend={self.tts_backend}, api_key={self.tts_api_key}, voice={self.tts_voice}')
            else:
                logging.warning(f'No se encontró configuración para agente {self.agent_name} en la base de datos.')
        except Exception as e:
            logging.error(f'Error al leer configuración TTS desde la base de datos: {str(e)}')

    def init_engine(self):
        if self.tts_backend == 'web_speech':
            logging.info('Backend web_speech seleccionado, TTS manejado por el frontend.')
            self.engine = None
        elif self.tts_backend == 'elevenlabs':
            if not self.tts_api_key:
                raise ValueError('API key de ElevenLabs requerida para este backend.')
            self.engine = ElevenLabs(api_key=self.tts_api_key)
            try:
                available_voices = self.engine.voices.get_all()
                voice_ids = [voice.voice_id for voice in available_voices.voices]
                logging.info(f'Voces disponibles en ElevenLabs: {voice_ids}')
                if self.tts_voice not in voice_ids:
                    logging.warning(f'Voz {self.tts_voice} no encontrada. Usando voz por defecto.')
                    self.tts_voice = voice_ids[0] if voice_ids else 'pBZVCk298iJlHAcHQwLr'  # Default to Leoni Vergara
                logging.info(f'Backend ElevenLabs inicializado con voz {self.tts_voice}')
            except Exception as e:
                logging.error(f'Error al obtener voces de ElevenLabs: {str(e)}')
                self.tts_voice = 'pBZVCk298iJlHAcHQwLr'  # Fallback to Leoni Vergara
        else:
            raise ValueError(f'Backend TTS no soportado: {self.tts_backend}')

    def speak(self, text, return_audio=True):
        if not text:
            logging.warning('No se proporcionó texto para reproducir.')
            return None

        self.text_buffer.append(text)
        current_time = time.time()
        diff = current_time - self.last_text_time if self.last_text_time is not None else self.buffer_timeout + 1

        audio = None
        if diff >= self.buffer_timeout or len(self.text_buffer) >= 5:  # Process if timeout or buffer size reached
            combined_text = " ".join(self.text_buffer)
            self.text_buffer = []  # Clear buffer
            audio = self._speak(combined_text, return_audio)

        self.last_text_time = current_time
        return audio

    def flush_buffer(self, return_audio=True):
        if not self.text_buffer:
            return None
        combined_text = " ".join(self.text_buffer)
        self.text_buffer = []
        self.last_text_time = None
        return self._speak(combined_text, return_audio)

    def _speak(self, text, return_audio):
        logging.info(f'Procesando texto con backend {self.tts_backend} en {self.tts_language}: {text}')
        if self.tts_backend == 'web_speech':
            return {'text': text, 'backend': 'web_speech', 'language': self.tts_language, 'voice': self.tts_voice}
        elif self.tts_backend == 'elevenlabs':
            try:
                audio_stream = self.engine.text_to_speech.convert(
                    text=text,
                    voice_id=self.tts_voice,
                    model_id='eleven_multilingual_v2',
                    output_format='mp3_44100_128',
                    previous_request_ids=self.previous_request_ids
                )
                audio_bytes = b''.join(audio_stream)
                request_id = getattr(audio_stream, 'request_id', str(time.time()))  # Fallback request_id
                self.previous_request_ids.append(request_id)
                self.previous_request_ids = self.previous_request_ids[-3:]  # Keep last 3
                logging.info(f'Request ID for stitching: {request_id}')
                if return_audio:
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                    logging.debug(f'Generated audio data (first 100 chars): {audio_base64[:100]}...')
                    return {'audio': audio_base64, 'backend': 'elevenlabs', 'mime_type': 'audio/mp3'}
                return None
            except Exception as e:
                logging.error(f'Error al generar audio con ElevenLabs: {str(e)}')
                return None