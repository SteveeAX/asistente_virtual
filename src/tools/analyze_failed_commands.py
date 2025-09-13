#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Herramienta para analizar comandos fallidos registrados por el sistema

Permite leer y analizar los comandos que no pudieron ser procesados
para identificar patrones y mejoras necesarias.

Autor: Asistente Kata
"""

import os
from typing import List, Dict, Any

def read_failed_commands(log_file: str = None) -> List[str]:
    """
    Lee los comandos fallidos del archivo de log
    
    Args:
        log_file: Ruta del archivo de log. Si None, usa la ruta por defecto
        
    Returns:
        List[str]: Lista de líneas del log de comandos fallidos
    """
    if log_file is None:
        # Usar ruta por defecto
        script_dir = os.path.dirname(__file__)
        log_file = os.path.join(script_dir, "..", "..", "data", "analysis", "failed_commands.txt")
    
    try:
        if not os.path.exists(log_file):
            print(f"⚠️  Archivo de log no encontrado: {log_file}")
            return []
        
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        print(f"📊 Leídos {len(lines)} registros de comandos fallidos")
        return [line.strip() for line in lines if line.strip()]
        
    except Exception as e:
        print(f"❌ Error leyendo archivo de log: {e}")
        return []

def analyze_failed_commands(lines: List[str]) -> Dict[str, Any]:
    """
    Analiza los comandos fallidos para identificar patrones
    
    Args:
        lines: Líneas del log de comandos fallidos
        
    Returns:
        Dict: Análisis de los patrones encontrados
    """
    analysis = {
        "total_failures": len(lines),
        "by_user": {},
        "by_reason": {},
        "common_words": {},
        "examples": []
    }
    
    for line in lines:
        # Formato esperado: "2025-01-01 12:00:00 [Usuario: Name] - FALLÓ: 'comando' [Razón: reason]"
        try:
            # Extraer usuario
            if "[Usuario: " in line:
                user_start = line.find("[Usuario: ") + 10
                user_end = line.find("]", user_start)
                user = line[user_start:user_end]
                analysis["by_user"][user] = analysis["by_user"].get(user, 0) + 1
            
            # Extraer comando fallido
            if "FALLÓ: '" in line:
                cmd_start = line.find("FALLÓ: '") + 8
                cmd_end = line.find("'", cmd_start)
                command = line[cmd_start:cmd_end]
                
                # Guardar ejemplos
                if len(analysis["examples"]) < 10:
                    analysis["examples"].append(command)
                
                # Contar palabras comunes
                words = command.lower().split()
                for word in words:
                    if len(word) > 2:  # Ignorar palabras muy cortas
                        analysis["common_words"][word] = analysis["common_words"].get(word, 0) + 1
            
            # Extraer razón del fallo
            if "[Razón: " in line:
                reason_start = line.find("[Razón: ") + 8
                reason_end = line.find("]", reason_start)
                reason = line[reason_start:reason_end]
                analysis["by_reason"][reason] = analysis["by_reason"].get(reason, 0) + 1
        
        except Exception:
            continue  # Ignorar líneas mal formateadas
    
    return analysis

def print_analysis_report(analysis: Dict[str, Any]):
    """
    Imprime un reporte legible del análisis
    
    Args:
        analysis: Resultado del análisis de comandos fallidos
    """
    print("\n" + "="*60)
    print("📋 REPORTE DE ANÁLISIS - COMANDOS FALLIDOS")
    print("="*60)
    
    print(f"\n📊 Total de fallos registrados: {analysis['total_failures']}")
    
    # Fallos por usuario
    if analysis['by_user']:
        print("\n👥 Fallos por usuario:")
        for user, count in sorted(analysis['by_user'].items(), key=lambda x: x[1], reverse=True):
            print(f"   • {user}: {count} fallos")
    
    # Fallos por razón
    if analysis['by_reason']:
        print("\n🔍 Razones de fallos:")
        for reason, count in sorted(analysis['by_reason'].items(), key=lambda x: x[1], reverse=True):
            print(f"   • {reason}: {count} veces")
    
    # Palabras más comunes en comandos fallidos
    if analysis['common_words']:
        print("\n🏷️  Palabras más comunes en fallos:")
        sorted_words = sorted(analysis['common_words'].items(), key=lambda x: x[1], reverse=True)[:10]
        for word, count in sorted_words:
            print(f"   • '{word}': {count} veces")
    
    # Ejemplos de comandos fallidos
    if analysis['examples']:
        print("\n💡 Ejemplos de comandos que fallaron:")
        for i, example in enumerate(analysis['examples'][:5], 1):
            print(f"   {i}. '{example}'")
    
    print("\n" + "="*60)

def main():
    """Función principal para ejecutar el análisis"""
    print("🔍 Analizando comandos fallidos del Asistente Kata...")
    
    # Leer comandos fallidos
    failed_lines = read_failed_commands()
    
    if not failed_lines:
        print("ℹ️  No hay comandos fallidos para analizar.")
        return
    
    # Analizar patrones
    analysis = analyze_failed_commands(failed_lines)
    
    # Mostrar reporte
    print_analysis_report(analysis)
    
    print("\n💡 Sugerencias:")
    print("   • Revisar patrones comunes en palabras frecuentes")
    print("   • Considerar agregar nuevos alias para contactos")
    print("   • Evaluar nuevos patrones de reconocimiento")

if __name__ == "__main__":
    main()