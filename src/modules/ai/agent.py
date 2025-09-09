import sqlite3
import json
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import Document
import os
import re
from config.settings import DB_PATH, EMBEDDING_MODEL, DEFAULT_AGENT_NAME, DEFAULT_SYSTEM_PROMPT, DEFAULT_BACKEND, DEFAULT_MODEL
from src.modules.tts_stt.tts import TTS  # Usar importación absoluta para evitar problemas

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

class AI_Agent:
    def __init__(self, agent_name=DEFAULT_AGENT_NAME):
        self.agent_name = agent_name
        self.load_agent_config()
        self.load_knowledge()
        self.init_llm()
        self.init_chain()
        try:
            print(f"Importing TTS: {TTS}, type: {type(TTS)}")
            print(f"Initializing TTS with extra_data: {self.extra_data}")
            self.tts = TTS(
                tts_backend=self.extra_data.get('tts_backend', 'web_speech'),
                tts_language=self.extra_data.get('tts_language', 'es-MX'),
                tts_voice=self.extra_data.get('tts_voice', 'Rachel'),
                tts_api_key=self.extra_data.get('tts_api_key', ''),
                agent_name=self.agent_name
            )
            print(f'TTS inicializado para {self.agent_name} con backend: {self.extra_data.get("tts_backend")}')
        except Exception as e:
            print(f'Error inicializando TTS: {str(e)}')
            self.tts = None

    def load_agent_config(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM agents WHERE name = ?', (self.agent_name,))
        agent_data = cursor.fetchone()
        conn.close()
        if agent_data:
            self.id, self.name, self.backend, self.model, self.system_prompt, self.forbidden_topics, self.must_say_no, self.verbosity_level, self.require_citation, self.max_words_response, self.language, self.extra_data, self.allowed_topics = agent_data
            self.forbidden_topics = self.forbidden_topics.split(',') if self.forbidden_topics else []
            self.allowed_topics = self.allowed_topics.split(',') if self.allowed_topics else []
            self.extra_data = json.loads(self.extra_data) if self.extra_data else {}
            print(f'Configuración del agente {self.name}: allowed_topics={self.allowed_topics}, forbidden_topics={self.forbidden_topics}')
        else:
            print(f'Agente {self.agent_name} no encontrado en la base de datos. Usando defaults.')
            self.backend = DEFAULT_BACKEND
            self.model = DEFAULT_MODEL
            self.system_prompt = DEFAULT_SYSTEM_PROMPT
            self.forbidden_topics = []
            self.allowed_topics = []
            self.must_say_no = 'No sé.'
            self.verbosity_level = 1
            self.require_citation = True
            self.max_words_response = 200
            self.language = 'es-MX'
            self.extra_data = {}

    def load_knowledge(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT fact, source FROM knowledge WHERE agent_id = (SELECT id FROM agents WHERE name = ?)', (self.agent_name,))
            docs = [Document(page_content=fact, metadata={'source': source or 'unknown'}) for fact, source in cursor.fetchall()]
            conn.close()
            if docs:
                self.vectorstore = FAISS.from_documents(docs, embeddings)
                print(f'Conocimiento cargado para {self.agent_name}: {len(docs)} documentos')
            else:
                self.vectorstore = None
                print(f'No se encontró conocimiento para {self.agent_name}')
        except Exception as e:
            print(f'Error cargando conocimiento: {str(e)}')
            self.vectorstore = None

    def init_llm(self):
        try:
            if self.backend == 'openai':
                self.llm = ChatOpenAI(model=self.model, api_key=os.getenv('OPENAI_API_KEY'))
            elif self.backend == 'grok':
                if ChatGroq is None:
                    raise ValueError('Backend "grok" no soportado: langchain_groq no está instalado.')
                self.llm = ChatGroq(model=self.model, api_key=os.getenv('GROK_API_KEY'))
            elif self.backend == 'ollama':
                self.llm = Ollama(model=self.model)
            else:
                raise ValueError('Backend no soportado')
            print(f'LLM inicializado: {self.backend}/{self.model}')
        except Exception as e:
            print(f'Error inicializando LLM: {str(e)}')
            raise

    def init_chain(self):
        try:
            prompt_str = (
                f"{self.system_prompt}\n"
                "IMPORTANTE: Responde EXCLUSIVAMENTE sobre los temas permitidos. Si la consulta no está relacionada con estos temas o contiene temas prohibidos, responde ÚNICAMENTE con: '{self.must_say_no}'.\n"
            )
            if self.forbidden_topics:
                prompt_str += f"Temas prohibidos: {', '.join(self.forbidden_topics)}. Responde con '{self.must_say_no}' si se menciona.\n"
            if self.allowed_topics:
                prompt_str += f"Temas permitidos: {', '.join(self.allowed_topics)}. Responde solo si la consulta se relaciona con estos temas.\n"
            if self.verbosity_level == 1:
                prompt_str += "Sé conciso.\n"
            elif self.verbosity_level == 3:
                prompt_str += "Sé detallado.\n"
            prompt_str += "Contexto: {context}\n"
            self.prompt_template = ChatPromptTemplate.from_messages([('system', prompt_str), ('human', '{query}')])
            if self.vectorstore:
                self.chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type='stuff',
                    retriever=self.vectorstore.as_retriever(search_kwargs={'k': 3}),
                    input_key='query',
                    return_source_documents=True
                )
            else:
                self.chain = self.prompt_template | self.llm
            print(f'Chain inicializado para {self.agent_name}')
        except Exception as e:
            print(f'Error inicializando chain: {str(e)}')
            raise

    def is_topic_related(self, query):
        print(f'Verificando consulta: "{query}"')
        print(f'Temas permitidos: {self.allowed_topics}')
        print(f'Temas prohibidos: {self.forbidden_topics}')
        
        # Si no hay temas permitidos definidos, permitir todas las consultas
        if not self.allowed_topics:
            print(f'No hay temas permitidos definidos para {self.agent_name}. Permitiendo consulta.')
            return True
        
        query_lower = query.lower().strip()
        query_clean = re.sub(r'[^\w\s]', '', query_lower)
        query_words = query_clean.split()
        print(f'Consulta limpia: "{query_clean}", Palabras: {query_words}')
        
        # Verificar consultas muy cortas
        if len(query_words) < 2:
            print(f'Consulta "{query}" considerada vaga después de limpieza: {query_clean}')
            return False
        
        # Método 1: Coincidencia exacta mejorada (palabras completas)
        for keyword in self.allowed_topics:
            keyword_lower = keyword.lower().strip()
            # Buscar como palabra completa, no subcadena
            if keyword_lower in query_words or any(word.startswith(keyword_lower) for word in query_words if len(keyword_lower) > 2):
                print(f'Consulta "{query}" coincide exactamente con tema permitido: {keyword}')
                return True
        
        # Método 2: Similitud semántica usando embeddings
        try:
            # Obtener embeddings de la consulta
            query_embedding = embeddings.embed_query(query)
            
            # Calcular similitud con cada tema permitido
            max_similarity = 0.0
            best_match = None
            similarity_threshold = 0.7  # Umbral de similitud (ajustable)
            
            for topic in self.allowed_topics:
                topic_embedding = embeddings.embed_query(topic)
                
                # Calcular similitud coseno
                similarity = self._cosine_similarity(query_embedding, topic_embedding)
                print(f'Similitud entre "{query}" y "{topic}": {similarity:.3f}')
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = topic
            
            if max_similarity >= similarity_threshold:
                print(f'Consulta "{query}" relacionada semánticamente con "{best_match}" (similitud: {max_similarity:.3f})')
                return True
            else:
                print(f'Consulta "{query}" no alcanza el umbral de similitud ({similarity_threshold}). Mejor coincidencia: "{best_match}" con {max_similarity:.3f}')
                
        except Exception as e:
            print(f'Error en verificación semántica: {str(e)}. Usando método exacto.')
        
        print(f'Consulta "{query}" no relacionada con temas permitidos.')
        return False
    
    def _cosine_similarity(self, vec1, vec2):
        """Calcula la similitud coseno entre dos vectores."""
        import numpy as np
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        return dot_product / (norm_vec1 * norm_vec2) if norm_vec1 != 0 and norm_vec2 != 0 else 0.0

    def get_response(self, query):
        if not self.is_topic_related(query):
            print(f'Consulta "{query}" no relacionada con temas permitidos. Retornando must_say_no.')
            return {'response': self.must_say_no}
        
        query_lower = query.lower().strip()
        for topic in self.forbidden_topics:
            if topic.lower() in query_lower or any(word in query_lower for word in topic.lower().split()):
                print(f'Consulta "{query}" contiene tema prohibido: {topic}. Retornando must_say_no.')
                return {'response': self.must_say_no}
        
        try:
            # Recuperar conocimiento relevante y construir contexto
            context = self._build_knowledge_context(query)
            
            if self.vectorstore:
                result = self.chain.invoke({'query': query})
                response = result['result']
                
                # Agregar contexto de conocimiento personalizado al inicio
                if context:
                    response = f"Basándome en mi conocimiento: {context}\n\n{response}"
                
                if self.require_citation:
                    sources = [doc.metadata['source'] for doc in result['source_documents']]
                    query_clean = re.sub(r'[^\w\s]', '', query_lower)
                    if not any(keyword.lower() in query_clean for keyword in self.allowed_topics):
                        print(f'Consulta "{query}" no relacionada con fuentes recuperadas. Retornando must_say_no.')
                        return {'response': self.must_say_no}
                    response += f'\nFuentes: {", ".join(sources)}'
            else:
                # Para agentes sin vectorstore, usar el contexto directamente en el prompt
                result = self.chain.invoke({'query': query, 'context': context})
                response = result.content
            
            response = ' '.join(response.split()[:self.max_words_response])
            print(f'Respuesta generada: {response}')
            
            audio_data = None
            if self.tts:
                try:
                    audio_data = self.tts.speak(response)
                except Exception as e:
                    print(f'Error al procesar audio con TTS: {str(e)}')
            
            return {'response': response, 'audio': audio_data}
        except Exception as e:
            print(f'Error generando respuesta: {str(e)}')
            return {'response': self.must_say_no}
    
    def _build_knowledge_context(self, query, max_facts=3):
        """Construye un contexto con los hechos más relevantes de la base de conocimiento."""
        if not self.vectorstore:
            return ""
        
        try:
            # Buscar documentos relevantes en la base de conocimiento
            relevant_docs = self.vectorstore.similarity_search(query, k=max_facts)
            
            if not relevant_docs:
                return ""
            
            # Construir el contexto con los hechos más relevantes
            facts = []
            for doc in relevant_docs:
                fact = doc.page_content.strip()
                source = doc.metadata.get('source', 'desconocida')
                facts.append(f"- {fact} (Fuente: {source})")
            
            context = "Información relevante que conozco:\n" + "\n".join(facts)
            print(f'Contexto de conocimiento construido: {context}')
            return context
            
        except Exception as e:
            print(f'Error construyendo contexto de conocimiento: {str(e)}')
            return ""

    def get_response_stream(self, query):
        if not self.is_topic_related(query):
            print(f'Consulta "{query}" no relacionada con temas permitidos. Retornando must_say_no.')
            yield {'response': self.must_say_no}
            return
        
        query_lower = query.lower().strip()
        for topic in self.forbidden_topics:
            if topic.lower() in query_lower or any(word in query_lower for word in topic.lower().split()):
                print(f'Consulta "{query}" contiene tema prohibido: {topic}. Retornando must_say_no.')
                yield {'response': self.must_say_no}
                return
        
        try:
            # Recuperar conocimiento relevante y construir contexto
            context = self._build_knowledge_context(query)
            
            if self.vectorstore:
                result = self.chain.invoke({'query': query})
                response = result['result']
                
                # Agregar contexto de conocimiento personalizado al inicio
                if context:
                    response = f"Basándome en mi conocimiento: {context}\n\n{response}"
                
                if self.require_citation:
                    sources = [doc.metadata['source'] for doc in result['source_documents']]
                    query_clean = re.sub(r'[^\w\s]', '', query_lower)
                    if not any(keyword.lower() in query_clean for keyword in self.allowed_topics):
                        print(f'Consulta "{query}" no relacionada con fuentes recuperadas. Retornando must_say_no.')
                        yield {'response': self.must_say_no}
                        return
                    response += f'\nFuentes: {", ".join(sources)}'
                
                # Streaming por palabras
                words = response.split()
                for i in range(0, len(words), 5):
                    chunk = ' '.join(words[i:i + 5]) + ' '
                    audio_data = None
                    if self.tts:
                        try:
                            audio_data = self.tts.speak(chunk)
                        except Exception as e:
                            print(f'Error al procesar audio con TTS: {str(e)}')
                    yield {'chunk': chunk, 'audio': audio_data}
                    if i + 5 >= self.max_words_response:
                        break
            else:
                words = []
                # Primero enviar el contexto si existe
                if context:
                    context_words = context.split()
                    for i in range(0, len(context_words), 5):
                        chunk_text = ' '.join(context_words[i:i + 5]) + ' '
                        audio_data = None
                        if self.tts:
                            try:
                                audio_data = self.tts.speak(chunk_text)
                            except Exception as e:
                                print(f'Error al procesar audio con TTS: {str(e)}')
                        yield {'chunk': chunk_text, 'audio': audio_data}
                        words.extend(context_words[i:i + 5])
                        if len(words) >= self.max_words_response:
                            break
                
                # Luego el streaming normal de la respuesta
                if len(words) < self.max_words_response:
                    for chunk in self.chain.stream({'query': query, 'context': context}):
                        content = chunk.content
                        chunk_words = content.split()
                        words.extend(chunk_words)
                        for i in range(0, len(chunk_words), 5):
                            chunk_text = ' '.join(chunk_words[i:i + 5]) + ' '
                            audio_data = None
                            if self.tts:
                                try:
                                    audio_data = self.tts.speak(chunk_text)
                                except Exception as e:
                                    print(f'Error al procesar audio con TTS: {str(e)}')
                            yield {'chunk': chunk_text, 'audio': audio_data}
                            if len(words) >= self.max_words_response:
                                break
        except Exception as e:
            print(f'Error generando stream: {str(e)}')
            yield {'response': self.must_say_no}

def add_agent(name, backend=DEFAULT_BACKEND, model=DEFAULT_MODEL, system_prompt=DEFAULT_SYSTEM_PROMPT, forbidden_topics='', must_say_no='No sé.', verbosity_level=1, require_citation=True, max_words_response=200, language='es-MX', extra_data='{}', allowed_topics=''):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO agents (name, backend, model, system_prompt, forbidden_topics, must_say_no, verbosity_level, require_citation, max_words_response, language, extra_data, allowed_topics)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, backend, model, system_prompt, forbidden_topics, must_say_no, verbosity_level, require_citation, max_words_response, language, extra_data, allowed_topics))
    conn.commit()
    conn.close()
    print(f'Agente "{name}" agregado/actualizado exitosamente.')

def add_knowledge(agent_name, fact, source=''):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO knowledge (agent_id, fact, source) VALUES ((SELECT id FROM agents WHERE name = ?), ?, ?)', (agent_name, fact, source))
    conn.commit()
    conn.close()
    print(f'Conocimiento agregado para agente "{agent_name}": {fact[:50]}...')

def list_agents():
    """Lista todos los agentes disponibles con su información básica."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name, backend, model, system_prompt FROM agents')
    agents = cursor.fetchall()
    conn.close()
    return [{'name': name, 'backend': backend, 'model': model, 'system_prompt': system_prompt[:100] + '...' if len(system_prompt) > 100 else system_prompt} for name, backend, model, system_prompt in agents]

def list_knowledge(agent_name):
    """Lista todo el conocimiento de un agente específico."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT k.id, k.fact, k.source 
    FROM knowledge k 
    JOIN agents a ON k.agent_id = a.id 
    WHERE a.name = ?
    ''', (agent_name,))
    knowledge = cursor.fetchall()
    conn.close()
    return [{'id': kid, 'fact': fact, 'source': source} for kid, fact, source in knowledge]

def update_knowledge(knowledge_id, new_fact, new_source=''):
    """Actualiza un hecho específico en la base de conocimiento."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE knowledge SET fact = ?, source = ? WHERE id = ?', (new_fact, new_source, knowledge_id))
    conn.commit()
    affected_rows = cursor.rowcount
    conn.close()
    if affected_rows > 0:
        print(f'Conocimiento ID {knowledge_id} actualizado exitosamente.')
        return True
    else:
        print(f'No se encontró conocimiento con ID {knowledge_id}.')
        return False

def delete_knowledge(knowledge_id):
    """Elimina un hecho específico de la base de conocimiento."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM knowledge WHERE id = ?', (knowledge_id,))
    conn.commit()
    affected_rows = cursor.rowcount
    conn.close()
    if affected_rows > 0:
        print(f'Conocimiento ID {knowledge_id} eliminado exitosamente.')
        return True
    else:
        print(f'No se encontró conocimiento con ID {knowledge_id}.')
        return False

def get_agent_stats(agent_name):
    """Obtiene estadísticas de un agente (cantidad de conocimiento, configuración, etc.)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Información del agente
    cursor.execute('SELECT * FROM agents WHERE name = ?', (agent_name,))
    agent_data = cursor.fetchone()
    
    if not agent_data:
        conn.close()
        return None
    
    # Contar conocimiento
    cursor.execute('SELECT COUNT(*) FROM knowledge WHERE agent_id = (SELECT id FROM agents WHERE name = ?)', (agent_name,))
    knowledge_count = cursor.fetchone()[0]
    
    conn.close()
    
    agent_info = {
        'name': agent_data[1],
        'backend': agent_data[2],
        'model': agent_data[3],
        'system_prompt': agent_data[4],
        'forbidden_topics': agent_data[5].split(',') if agent_data[5] else [],
        'must_say_no': agent_data[6],
        'verbosity_level': agent_data[7],
        'require_citation': bool(agent_data[8]),
        'max_words_response': agent_data[9],
        'language': agent_data[10],
        'extra_data': json.loads(agent_data[11]) if agent_data[11] else {},
        'allowed_topics': agent_data[12].split(',') if agent_data[12] else [],
        'knowledge_count': knowledge_count
    }
    
    return agent_info