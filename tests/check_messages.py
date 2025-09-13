#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script rápido para verificar mensajes en la BD
"""

import sys
import os

# Agregar path del proyecto
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.models.shared_data_manager import shared_data_manager

def check_messages():
    """Verifica mensajes en la base de datos"""
    print("🔍 Verificando mensajes en la base de datos...")
    
    try:
        # Contar mensajes no leídos
        count = shared_data_manager.get_unread_message_count()
        print(f"📊 Total mensajes no leídos: {count}")
        
        if count > 0:
            # Mostrar mensajes
            messages = shared_data_manager.get_unread_messages(limit=10)
            print(f"\n📨 Mensajes recientes:")
            
            for msg in messages:
                print(f"   • ID {msg['id']}: [{msg['contact_name']}] {msg['message_text'][:50]}...")
                print(f"     Recibido: {msg['received_at']}")
        else:
            print("📭 No hay mensajes no leídos")
            
    except Exception as e:
        print(f"❌ Error verificando mensajes: {e}")

if __name__ == "__main__":
    check_messages()