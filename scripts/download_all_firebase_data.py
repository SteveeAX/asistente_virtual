#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para descargar TODOS los datos de Firebase
"""

import os
import sys
from datetime import datetime, timedelta
import json

# Agregar ruta del proyecto
sys.path.append('/home/steveen/asistente_kata')

def download_all_firebase_data():
    """Descarga TODOS los datos de Firebase"""
    try:
        from google.cloud import firestore
        
        # Conectar a Firebase
        db = firestore.Client(database='asistente-kata-db')
        print("✅ Conectado a Firebase")
        
        # Obtener todas las colecciones
        collections = db.collections()
        print("🔍 Enumerando colecciones...")
        
        all_data = {}
        
        for collection_ref in collections:
            collection_name = collection_ref.id
            print(f"\n📂 Procesando colección: {collection_name}")
            
            try:
                # Obtener todos los documentos de la colección
                docs = collection_ref.stream()
                collection_data = []
                
                doc_count = 0
                for doc in docs:
                    doc_dict = doc.to_dict()
                    doc_dict['_firestore_id'] = doc.id  # Preservar ID del documento
                    collection_data.append(doc_dict)
                    doc_count += 1
                    
                    # Mostrar progreso cada 100 documentos
                    if doc_count % 100 == 0:
                        print(f"   📊 Procesados {doc_count} documentos...")
                
                all_data[collection_name] = collection_data
                print(f"   ✅ {collection_name}: {doc_count} documentos")
                
            except Exception as e:
                print(f"   ❌ Error procesando {collection_name}: {e}")
                continue
        
        # Guardar todos los datos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'/home/steveen/asistente_kata/data/analysis/firebase_complete_backup_{timestamp}.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        print(f"\n💾 Guardando datos completos...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Backup completo guardado en: {output_file}")
        
        # Mostrar resumen
        print(f"\n📋 RESUMEN DEL BACKUP")
        print("="*50)
        total_docs = 0
        for collection_name, data in all_data.items():
            count = len(data)
            total_docs += count
            print(f"📂 {collection_name}: {count} documentos")
        
        print(f"\n🎯 TOTAL: {total_docs} documentos en {len(all_data)} colecciones")
        
        # Si hay interaction_logs, hacer análisis específico
        if 'interaction_logs' in all_data:
            analyze_interaction_logs(all_data['interaction_logs'], timestamp)
        
        return all_data
        
    except Exception as e:
        print(f"❌ Error descargando datos de Firebase: {e}")
        return {}

def analyze_interaction_logs(interaction_logs, timestamp):
    """Analiza específicamente los logs de interacción"""
    print(f"\n🔍 ANÁLISIS DETALLADO DE INTERACTION_LOGS")
    print("="*60)
    
    # Contar tipos de eventos
    event_types = {}
    recent_failed = []
    all_transcriptions = []
    
    for log in interaction_logs:
        event_type = log.get('event_type', 'unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Recoger transcripciones si existen
        details = log.get('details', {})
        if 'transcription' in details:
            transcription = details['transcription']
            all_transcriptions.append({
                'text': transcription,
                'event_type': event_type,
                'timestamp': log.get('timestamp'),
                'route': details.get('route'),
                'fallback_reason': details.get('fallback_reason')
            })
            
            # Si es comando fallido, agregarlo a la lista
            if event_type == 'command_not_understood':
                recent_failed.append({
                    'transcription': transcription,
                    'timestamp': log.get('timestamp'),
                    'details': details
                })
    
    # Mostrar tipos de eventos
    print(f"📊 Tipos de eventos encontrados:")
    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {event_type}: {count} veces")
    
    # Guardar análisis detallado de transcripciones
    transcriptions_file = f'/home/steveen/asistente_kata/data/analysis/all_transcriptions_{timestamp}.json'
    with open(transcriptions_file, 'w', encoding='utf-8') as f:
        json.dump(all_transcriptions, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Todas las transcripciones guardadas en: {transcriptions_file}")
    
    # Mostrar estadísticas de comandos fallidos
    if recent_failed:
        print(f"\n❌ COMANDOS FALLIDOS ({len(recent_failed)} total):")
        for i, fail in enumerate(recent_failed[-10:], 1):  # Mostrar últimos 10
            timestamp_str = fail['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if fail.get('timestamp') else 'Sin fecha'
            print(f"   {i}. [{timestamp_str}] '{fail['transcription']}'")
    
    # Análisis de palabras en todas las transcripciones
    print(f"\n🔤 ANÁLISIS DE PALABRAS EN TODAS LAS TRANSCRIPCIONES:")
    word_count = {}
    for trans in all_transcriptions:
        text = trans.get('text', '').lower()
        if text and text != 'no disponible':
            words = text.split()
            for word in words:
                if len(word) > 2:
                    word_count[word] = word_count.get(word, 0) + 1
    
    if word_count:
        print("🏷️ Palabras más usadas:")
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        for word, count in sorted_words[:20]:
            print(f"   • '{word}': {count} veces")

if __name__ == "__main__":
    print("🚀 Descargando TODOS los datos de Firebase...")
    all_data = download_all_firebase_data()
    
    if all_data:
        print(f"\n🎉 Descarga completa finalizada exitosamente")
    else:
        print("❌ No se pudieron descargar los datos")