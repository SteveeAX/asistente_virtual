#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FailedCommandsLogger - Sistema simple de registro de comandos fallidos

Solo registra comandos que fallan para análisis posterior manual.
Sin retroalimentación automática ni complejidad innecesaria.

Autor: Asistente Kata
"""

import logging
import os
from datetime import datetime
from typing import Optional, List

logger = logging.getLogger(__name__)

class FailedCommandsLogger:
    """Logger simple de comandos fallidos"""
    
    def __init__(self, log_file_path: Optional[str] = None):
        """
        Inicializa el logger simple
        
        Args:
            log_file_path: Ruta del archivo de log. Si None, usa ruta por defecto
        """
        if log_file_path is None:
            # Usar directorio de datos
            data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "analysis")
            os.makedirs(data_dir, exist_ok=True)
            log_file_path = os.path.join(data_dir, "failed_commands.txt")
        
        self.log_file = log_file_path
        logger.info(f"FailedCommandsLogger: Guardando en {log_file_path}")
    
    def log_failed_command(self, original_text: str, user_name: Optional[str] = None, reason: Optional[str] = None):
        """
        Registra un comando fallido de forma simple
        
        Args:
            original_text: Texto original que falló
            user_name: Usuario (opcional)
            reason: Razón del fallo (opcional)
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_part = f" [Usuario: {user_name}]" if user_name else ""
            reason_part = f" [Razón: {reason}]" if reason else ""
            
            log_entry = f"{timestamp}{user_part} - FALLÓ: '{original_text}'{reason_part}\n"
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            
            logger.info(f"FailedCommandsLogger: Registrado - '{original_text}'")
            
        except Exception as e:
            logger.error(f"FailedCommandsLogger: Error escribiendo log: {e}")
    
    def get_recent_failures(self, lines: int = 50) -> List[str]:
        """
        Obtiene los últimos fallos registrados
        
        Args:
            lines: Número de líneas a leer
            
        Returns:
            List[str]: Últimas líneas del log
        """
        try:
            if not os.path.exists(self.log_file):
                return []
            
            with open(self.log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if all_lines else []
                
        except Exception as e:
            logger.error(f"FailedCommandsLogger: Error leyendo log: {e}")
            return []

# Instancia global simple
failed_logger: Optional[FailedCommandsLogger] = None

def initialize_failed_commands_logger() -> Optional[FailedCommandsLogger]:
    """Inicializa el logger global"""
    global failed_logger
    try:
        failed_logger = FailedCommandsLogger()
        return failed_logger
    except Exception as e:
        logger.error(f"Error inicializando FailedCommandsLogger: {e}")
        return None

def log_failed_command(text: str, user: Optional[str] = None, reason: Optional[str] = None):
    """Función de conveniencia para registrar fallos"""
    if failed_logger:
        failed_logger.log_failed_command(text, user, reason)