import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import BASE_DIR

DB_PATH = os.path.join(BASE_DIR, 'knowledge.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        backend TEXT DEFAULT 'ollama',
        model TEXT DEFAULT 'phi3:mini',
        system_prompt TEXT NOT NULL,
        forbidden_topics TEXT,
        must_say_no TEXT DEFAULT 'No sé o No puedo responder sobre eso.',
        verbosity_level INTEGER DEFAULT 1,
        require_citation BOOLEAN DEFAULT TRUE,
        max_words_response INTEGER DEFAULT 200,
        language TEXT DEFAULT 'es-MX',
        extra_data TEXT DEFAULT '{}',
        allowed_topics TEXT DEFAULT ''  -- Palabras clave para temas permitidos (coma-separado)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER NOT NULL,
        fact TEXT NOT NULL,
        source TEXT,
        embedding BLOB,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f'DB inicializada en {DB_PATH}')

if __name__ == '__main__':
    init_db()