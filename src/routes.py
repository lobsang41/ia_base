from flask import Flask, render_template, request, jsonify, Response
from modules.ai.agent import AI_Agent, add_agent, add_knowledge, list_agents as get_all_agents, list_knowledge, update_knowledge, delete_knowledge, get_agent_stats
from modules.tts_stt.stt import STT
from config.settings import DEFAULT_AGENT_NAME, DB_PATH
import json
import logging
import sqlite3
import os

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logging.debug(f"DB_PATH: {DB_PATH}")

def register_routes(app):
    stt = STT()

    @app.route('/')
    def index():
        """Renderiza la página principal del chat."""
        return render_template('index.html')

    @app.route('/ai_response', methods=['POST'])
    def ai_response():
        """Procesa un mensaje de chat y devuelve la respuesta del agente en streaming."""
        data = request.json
        query = data.get('query', '')
        agent_name = data.get('agent_name', DEFAULT_AGENT_NAME)
        try:
            agent = AI_Agent(agent_name)
            def generate():
                response_text = ''
                try:
                    for item in agent.get_response_stream(query):
                        if isinstance(item, dict) and 'chunk' in item:
                            chunk = item['chunk']
                            audio_data = item.get('audio')
                            if chunk.strip():
                                response_text += chunk
                                yield json.dumps({
                                    'response': chunk,
                                    'audio': audio_data,
                                    'agent': agent_name
                                }) + '\n'
                        else:
                            response = item.get('response', 'No tengo información sobre eso.') if isinstance(item, dict) else item
                            audio_data = item.get('audio') if isinstance(item, dict) else None
                            yield json.dumps({
                                'response': response,
                                'audio': audio_data,
                                'agent': agent_name
                            }) + '\n'
                            return
                except Exception as e:
                    logging.error(f'Error en generate: {str(e)}')
                    yield json.dumps({
                        'response': f'Error en la respuesta: {str(e)}',
                        'agent': agent_name
                    }) + '\n'
            return Response(generate(), mimetype='application/json')
        except Exception as e:
            logging.error(f'Error en ai_response: {str(e)}')
            return jsonify({'response': f'Error en la respuesta: {str(e)}', 'agent': agent_name}), 500

    @app.route('/tts', methods=['POST'])
    def tts_speak():
        """Envía texto para reproducir con Web Speech en el frontend."""
        data = request.json
        text = data.get('text', '')
        language = data.get('language', 'es-MX')
        voice = data.get('voice', 'male')
        if not text:
            return jsonify({'error': 'No se proporcionó texto'}), 400
        return jsonify({'text': text, 'language': language, 'voice': voice})

    @app.route('/stt', methods=['POST'])
    def speech_to_text():
        """Convierte voz a texto usando STT."""
        try:
            text = stt.listen()
            return jsonify({'text': text})
        except Exception as e:
            logging.error(f'Error en stt: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/create_agent', methods=['POST'])
    def create_agent():
        """Crea un nuevo agente con configuración personalizada."""
        data = request.json
        try:
            add_agent(
                name=data.get('name', 'NewAgent'),
                backend=data.get('backend', 'ollama'),
                model=data.get('model', 'phi3:mini'),
                system_prompt=data.get('system_prompt', 'Eres un asistente útil.'),
                forbidden_topics=data.get('forbidden_topics', ''),
                must_say_no=data.get('must_say_no', 'No sé.'),
                verbosity_level=data.get('verbosity_level', 1),
                require_citation=data.get('require_citation', True),
                max_words_response=data.get('max_words_response', 200),
                language=data.get('language', 'es-MX'),
                extra_data=data.get('extra_data', '{}'),
                allowed_topics=data.get('allowed_topics', '')
            )
            return jsonify({'status': 'Agente creado exitosamente'})
        except Exception as e:
            logging.error(f'Error en create_agent: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/add_knowledge', methods=['POST'])
    def add_knowledge_route():
        """Agrega un nuevo hecho a la base de conocimiento de un agente."""
        data = request.json
        try:
            add_knowledge(
                agent_name=data.get('agent_name', DEFAULT_AGENT_NAME),
                fact=data.get('fact', ''),
                source=data.get('source', 'unknown')
            )
            return jsonify({'status': 'Conocimiento agregado exitosamente'})
        except Exception as e:
            logging.error(f'Error en add_knowledge: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/list_agents', methods=['GET'])
    def list_agents():
        """Devuelve una lista de agentes disponibles."""
        try:
            agents = get_all_agents()
            logging.debug(f'Agentes encontrados: {agents}')
            return jsonify({'agents': agents})
        except Exception as e:
            logging.error(f'Error en list_agents: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/list_knowledge/<agent_name>', methods=['GET'])
    def list_knowledge_route(agent_name):
        """Lista todo el conocimiento de un agente específico."""
        try:
            knowledge = list_knowledge(agent_name)
            return jsonify({'knowledge': knowledge, 'agent_name': agent_name})
        except Exception as e:
            logging.error(f'Error en list_knowledge: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/update_knowledge', methods=['PUT'])
    def update_knowledge_route():
        """Actualiza un hecho específico en la base de conocimiento."""
        data = request.json
        try:
            success = update_knowledge(
                knowledge_id=data.get('id'),
                new_fact=data.get('fact', ''),
                new_source=data.get('source', '')
            )
            if success:
                return jsonify({'status': 'Conocimiento actualizado exitosamente'})
            else:
                return jsonify({'error': 'No se encontró el conocimiento especificado'}), 404
        except Exception as e:
            logging.error(f'Error en update_knowledge: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/delete_knowledge/<int:knowledge_id>', methods=['DELETE'])
    def delete_knowledge_route(knowledge_id):
        """Elimina un hecho específico de la base de conocimiento."""
        try:
            success = delete_knowledge(knowledge_id)
            if success:
                return jsonify({'status': 'Conocimiento eliminado exitosamente'})
            else:
                return jsonify({'error': 'No se encontró el conocimiento especificado'}), 404
        except Exception as e:
            logging.error(f'Error en delete_knowledge: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/agent_stats/<agent_name>', methods=['GET'])
    def agent_stats_route(agent_name):
        """Obtiene estadísticas detalladas de un agente."""
        try:
            stats = get_agent_stats(agent_name)
            if stats:
                return jsonify({'stats': stats})
            else:
                return jsonify({'error': 'Agente no encontrado'}), 404
        except Exception as e:
            logging.error(f'Error en agent_stats: {str(e)}')
            return jsonify({'error': str(e)}), 500