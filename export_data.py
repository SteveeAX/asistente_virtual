# export_data.py
import os
import logging
import csv
from google.cloud import firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    # Usa el mismo método de autenticación que tu app principal
    db = firestore.Client()
    logging.info("Conexión con Cloud Firestore establecida.")

    # Nombre del archivo de salida
    output_filename = "interaction_logs.csv"

    # Obtenemos todos los documentos de la colección
    docs = db.collection('interaction_logs').order_by('timestamp').stream()

    logging.info(f"Exportando datos a {output_filename}...")

    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        # Definimos las columnas que queremos en el CSV
        fieldnames = ['timestamp', 'event_type', 'transcription', 'command']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

        # Escribimos la cabecera
        writer.writeheader()

        count = 0
        # Iteramos sobre cada documento y lo escribimos en el archivo
        for doc in docs:
            log_data = doc.to_dict()

            # Aplanamos el diccionario de 'details' para facilitar la lectura
            flat_data = {
                'timestamp': log_data.get('timestamp'),
                'event_type': log_data.get('event_type'),
                'transcription': log_data.get('details', {}).get('transcription'),
                'command': log_data.get('details', {}).get('command')
            }
            writer.writerow(flat_data)
            count += 1

    logging.info(f"¡Éxito! Se han exportado {count} registros a {output_filename}.")

except Exception as e:
    logging.error(f"Ocurrió un error durante la exportación: {e}")
