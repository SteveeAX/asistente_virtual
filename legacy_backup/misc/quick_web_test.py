#!/usr/bin/env python3
"""
Script rápido para probar el gestor web con los campos corregidos.
"""

import subprocess
import time
import webbrowser
import os
import signal
import sys

def start_server():
    """Inicia el servidor web"""
    print("🌐 Iniciando servidor web...")
    try:
        # Cambiar al directorio del proyecto
        os.chdir('/home/steveen/asistente_kata')
        
        # Iniciar servidor
        process = subprocess.Popen([sys.executable, 'web_server.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Dar tiempo para que inicie
        time.sleep(3)
        
        # Verificar si el proceso está corriendo
        if process.poll() is None:
            print("✅ Servidor web iniciado correctamente")
            print("🌐 URL: http://localhost:5000")
            
            # Abrir archivo de prueba local para comparar
            test_file_path = os.path.abspath('test_form_layout.html')
            print(f"🧪 Archivo de prueba: file://{test_file_path}")
            
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Error iniciando servidor:")
            print(f"stdout: {stdout.decode()}")
            print(f"stderr: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("=" * 60)
    print("🧪 PRUEBA RÁPIDA DEL GESTOR WEB CORREGIDO")
    print("=" * 60)
    
    print("\n📋 Cambios aplicados:")
    print("✅ CSS corregido: align-items: start")
    print("✅ Textarea incluido en estilos CSS")
    print("✅ Padding mejorado para labels")
    print("✅ Visualización mejorada en tabla")
    
    print("\n" + "=" * 40)
    print("OPCIONES:")
    print("1. 🌐 Iniciar servidor web real")
    print("2. 🧪 Abrir archivo de prueba local")
    print("3. ❌ Salir")
    print("=" * 40)
    
    choice = input("Selecciona una opción (1-3): ").strip()
    
    if choice == "1":
        process = start_server()
        if process:
            print("\n🎯 INSTRUCCIONES DE PRUEBA:")
            print("1. Ve a http://localhost:5000")
            print("2. Busca el formulario 'Añadir Recordatorio'")
            print("3. Verifica que aparezcan estos campos:")
            print("   📋 Medicamento")
            print("   💊 Cantidad")
            print("   📝 Prescripción (textarea)")
            print("   ⏰ Horas")
            print("   📅 Días")
            print("   🖼️ Foto")
            print("4. Llena el formulario y envía")
            
            try:
                input("\nPresiona Enter cuando hayas terminado...")
                print("🛑 Cerrando servidor...")
                process.terminate()
                process.wait()
                print("✅ Servidor cerrado")
            except KeyboardInterrupt:
                print("\n🛑 Cerrando servidor...")
                process.terminate()
                process.wait()
                
    elif choice == "2":
        test_file = os.path.abspath('/home/steveen/asistente_kata/test_form_layout.html')
        print(f"\n🧪 Abriendo archivo de prueba...")
        print(f"📁 {test_file}")
        
        if os.path.exists(test_file):
            print("\n🎯 En el archivo de prueba deberías ver:")
            print("✅ Formulario con campos correctamente alineados")
            print("✅ Campo 'Cantidad' como input de texto")
            print("✅ Campo 'Prescripción' como textarea")
            print("✅ Tabla de ejemplo con datos formateados")
            
            # Abrir en navegador por defecto
            webbrowser.open(f'file://{test_file}')
            input("\nPresiona Enter cuando hayas revisado el archivo...")
        else:
            print("❌ Archivo de prueba no encontrado")
            
    elif choice == "3":
        print("👋 ¡Hasta luego!")
    else:
        print("❌ Opción inválida")

if __name__ == "__main__":
    main()