import os
import sys
import json

# Agrega el directorio raíz al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.ai.agent import add_agent, add_knowledge
from config.settings import DEFAULT_BACKEND, DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT, DEFAULT_MAX_WORDS_RESPONSE, DEFAULT_LANGUAGE, DEFAULT_EXTRA_DATA

# Definir agentes y conocimientos
add_agent(
    name='TechAgent',
    backend=DEFAULT_BACKEND,
    model=DEFAULT_MODEL,
    system_prompt='Eres un experto en programación, software, hardware y tecnología. Responde EXCLUSIVAMENTE sobre temas de tecnología. Ignora cualquier pregunta que no esté relacionada con tecnología y responde con la frase configurada en must_say_no.',
    forbidden_topics='política,religión,datos personales,geografía,clima,historia,deportes,ciencia natural',
    must_say_no='Lo siento, solo puedo responder sobre temas de tecnología.',
    verbosity_level=2,
    require_citation=True,
    max_words_response=DEFAULT_MAX_WORDS_RESPONSE,
    language='es-MX',
    extra_data=json.dumps({'tts_backend': 'web_speech', 'tts_language': 'es-MX', 'tts_voice': 'male', 'tts_api_key': ''}),
    allowed_topics='programación,software,hardware,tecnología,computadora,sistema,aplicación,framework,python,flask,tts,stt,api,código,programa,desarrollo,internet,red,servidor,base de datos,sql,algoritmo,inteligencia artificial,navegador,chrome'
)
add_knowledge('TechAgent', 'Flask es un framework web ligero para Python.', 'docs/flask.txt')
add_knowledge('TechAgent', 'pyttsx3 se usa para TTS offline.', 'docs/pyttsx3.txt')
add_knowledge('TechAgent', 'Chrome es un navegador web desarrollado por Google.', 'docs/chrome.txt')
add_knowledge('TechAgent', 'SQL es un lenguaje de consulta estructurado para gestionar bases de datos relacionales.', 'docs/sql.txt')

add_agent(
    name='FoodAgent',
    backend=DEFAULT_BACKEND,
    model=DEFAULT_MODEL,
    system_prompt='Eres un experto en comida, recetas y nutrición. Responde EXCLUSIVAMENTE sobre temas de comida.',
    forbidden_topics='política,religión,datos personales',
    must_say_no='Lo siento, solo puedo responder sobre temas de comida.',
    verbosity_level=2,
    require_citation=True,
    max_words_response=DEFAULT_MAX_WORDS_RESPONSE,
    language='es-MX',
    extra_data=json.dumps({'tts_backend': 'web_speech', 'tts_language': 'es-MX', 'tts_voice': 'female', 'tts_api_key': ''}),
    allowed_topics='comida,recetas,ingredientes,nutrición,alimentos,cocina,platos,diets,salud alimentaria'
)
add_knowledge('FoodAgent', 'La pizza es un plato italiano con masa, salsa de tomate y queso.', 'docs/food.txt')

add_agent(
    name='DefaultAgent',
    backend=DEFAULT_BACKEND,
    model=DEFAULT_MODEL,
    system_prompt='Eres un asistente general. Responde amigablemente sobre cualquier tema permitido.',
    forbidden_topics='datos personales',
    must_say_no='No tengo información sobre eso.',
    verbosity_level=1,
    require_citation=False,
    max_words_response=DEFAULT_MAX_WORDS_RESPONSE,
    language='es-MX',
    extra_data=json.dumps({'tts_backend': 'web_speech', 'tts_language': 'es-MX', 'tts_voice': 'male', 'tts_api_key': ''}),
    allowed_topics=''  # No filtra temas
)
add_knowledge('DefaultAgent', 'El clima puede variar según la región.', 'docs/weather.txt')

print("Agentes y conocimientos inicializados correctamente.")