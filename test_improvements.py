#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras implementadas en el proyecto ia_base.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.ai.agent import AI_Agent, list_agents, list_knowledge, get_agent_stats

def test_semantic_filtering():
    """Prueba el filtro semántico mejorado."""
    print("=== PRUEBA 1: Filtro Semántico Mejorado ===")
    
    # Crear agente de tecnología
    tech_agent = AI_Agent('TechAgent')
    
    # Pruebas de consultas relacionadas con tecnología
    tech_queries = [
        "¿Qué es Python?",  # Debería pasar (relacionado con programación)
        "Quiero aprender sobre desarrollo web",  # Debería pasar (relacionado con desarrollo)
        "¿Cómo funciona una computadora?",  # Debería pasar (relacionado con hardware)
        "¿Cuál es la capital de Francia?",  # No debería pasar (geografía)
        "¿Qué tiempo hace hoy?",  # No debería pasar (clima)
    ]
    
    for query in tech_queries:
        is_related = tech_agent.is_topic_related(query)
        print(f"Consulta: '{query}' -> Relacionada: {is_related}")
    
    print()

def test_knowledge_context():
    """Prueba la inclusión de conocimiento en el contexto."""
    print("=== PRUEBA 2: Contexto de Conocimiento ===")
    
    tech_agent = AI_Agent('TechAgent')
    
    # Consulta que debería activar el conocimiento sobre Flask
    query = "¿Qué es Flask?"
    context = tech_agent._build_knowledge_context(query)
    
    print(f"Consulta: {query}")
    print(f"Contexto generado: {context}")
    print()

def test_agent_management():
    """Prueba las nuevas funciones de gestión de agentes."""
    print("=== PRUEBA 3: Gestión de Agentes ===")
    
    # Listar agentes
    agents = list_agents()
    print(f"Agentes disponibles: {len(agents)}")
    for agent in agents:
        print(f"  - {agent['name']} ({agent['backend']}/{agent['model']})")
    
    print()
    
    # Estadísticas de agente
    if agents:
        agent_name = agents[0]['name']
        stats = get_agent_stats(agent_name)
        print(f"Estadísticas de {agent_name}:")
        print(f"  - Conocimientos: {stats['knowledge_count']}")
        print(f"  - Temas permitidos: {len(stats['allowed_topics'])}")
        print(f"  - Temas prohibidos: {len(stats['forbidden_topics'])}")
        print(f"  - Máximo de palabras: {stats['max_words_response']}")
    
    print()

def test_knowledge_management():
    """Prueba la gestión del conocimiento."""
    print("=== PRUEBA 4: Gestión de Conocimiento ===")
    
    # Listar conocimiento del TechAgent
    knowledge = list_knowledge('TechAgent')
    print(f"Conocimientos de TechAgent: {len(knowledge)}")
    for k in knowledge[:3]:  # Mostrar solo los primeros 3
        print(f"  - ID {k['id']}: {k['fact'][:50]}...")
    
    print()

def main():
    """Ejecuta todas las pruebas."""
    print("🚀 INICIANDO PRUEBAS DE MEJORAS IMPLEMENTADAS\n")
    
    try:
        test_semantic_filtering()
        test_knowledge_context()
        test_agent_management()
        test_knowledge_management()
        
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        
    except Exception as e:
        print(f"❌ ERROR EN LAS PRUEBAS: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
