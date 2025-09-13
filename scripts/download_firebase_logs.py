#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para descargar logs de comandos fallidos desde Firebase
Autor: Claude Code
"""

import os
import sys
from datetime import datetime, timedelta
import json

# Agregar ruta del proyecto
sys.path.append('/home/steveen/asistente_kata')

def download_failed_commands():
    """Descarga comandos fallidos desde Firebase"""
    try:
        from google.cloud import firestore
        
        # Conectar a Firebase
        db = firestore.Client(database='asistente-kata-db')
        print("✅ Conectado a Firebase")
        
        # Obtener colección de logs
        logs_collection = db.collection('interaction_logs')
        
        print("🔍 Buscando comandos no entendidos...")
        
        # Query más simple - solo filtrar por tipo de evento
        failed_commands_query = logs_collection.where(
            'event_type', '==', 'command_not_understood'
        ).limit(100)
        
        failed_commands = failed_commands_query.get()
        
        print(f"📊 Encontrados {len(failed_commands)} comandos fallidos")
        
        # Procesar resultados
        results = []
        for doc in failed_commands:
            data = doc.to_dict()
            result = {
                'id': doc.id,
                'timestamp': data.get('timestamp'),
                'event_type': data.get('event_type'),
                'transcription': data.get('details', {}).get('transcription', 'No disponible'),
                'route': data.get('details', {}).get('route', 'No disponible'),
                'fallback_reason': data.get('details', {}).get('fallback_reason', None)
            }
            results.append(result)
            
            # Mostrar comando
            timestamp_str = result['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if result['timestamp'] else 'Sin fecha'
            print(f"❌ [{timestamp_str}] '{result['transcription']}'")
        
        # Guardar en archivo JSON
        output_file = '/home/steveen/asistente_kata/data/analysis/firebase_failed_commands.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Datos guardados en: {output_file}")
        
        # También buscar otros tipos de fallos
        print("\n🔍 Buscando otros tipos de eventos de interés...")
        
        # Buscar eventos de IA generativa que podrían ser fallos
        ai_fallback_query = logs_collection.where(
            'event_type', '==', 'ai_query'
        ).limit(50)
        
        ai_events = ai_fallback_query.get()
        print(f"🤖 Encontrados {len(ai_events)} eventos de IA recientes")
        
        # Mostrar algunos ejemplos
        for i, doc in enumerate(ai_events[:10]):
            data = doc.to_dict()
            transcription = data.get('details', {}).get('transcription', 'No disponible')
            timestamp_str = data.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if data.get('timestamp') else 'Sin fecha'
            print(f"🤖 [{timestamp_str}] '{transcription}'")
        
        return results
        
    except Exception as e:
        print(f"❌ Error descargando datos de Firebase: {e}")
        return []

def analyze_failed_patterns(failed_commands):
    """Analiza patrones en comandos fallidos"""
    if not failed_commands:
        print("⚠️ No hay comandos fallidos para analizar")
        return
    
    print(f"\n📋 ANÁLISIS DE {len(failed_commands)} COMANDOS FALLIDOS")
    print("="*60)
    
    # Agrupar por palabras comunes
    word_count = {}
    for cmd in failed_commands:
        transcription = cmd.get('transcription', '').lower()
        if transcription and transcription != 'no disponible':
            words = transcription.split()
            for word in words:
                if len(word) > 2:  # Ignorar palabras muy cortas
                    word_count[word] = word_count.get(word, 0) + 1
    
    # Mostrar palabras más comunes
    if word_count:
        print("\n🏷️ Palabras más comunes en comandos fallidos:")
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        for word, count in sorted_words[:10]:
            print(f"   • '{word}': {count} veces")
    
    # Mostrar algunos ejemplos
    print(f"\n💡 Ejemplos de comandos que fallaron:")
    for i, cmd in enumerate(failed_commands[:10], 1):
        transcription = cmd.get('transcription', 'No disponible')
        timestamp_str = cmd.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if cmd.get('timestamp') else 'Sin fecha'
        print(f"   {i}. [{timestamp_str}] '{transcription}'")

if __name__ == "__main__":
    print("🔍 Descargando comandos fallidos desde Firebase...")
    failed_commands = download_failed_commands()
    
    if failed_commands:
        analyze_failed_patterns(failed_commands)
        print(f"\n✅ Proceso completado. Datos guardados en data/analysis/firebase_failed_commands.json")
    else:
        print("❌ No se pudieron descargar datos")