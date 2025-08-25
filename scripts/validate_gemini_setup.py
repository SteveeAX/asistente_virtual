#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de validación rápida para verificar que la integración con Gemini
está funcionando correctamente antes de usar en producción.

Autor: Asistente Kata
Fecha: 2024-08-16
Versión: 1.0.0
"""

import sys
import os

# Agregar directorios al path
project_dir = "/home/steveen/asistente_kata"
modules_dir = os.path.join(project_dir, "modules")
sys.path.insert(0, modules_dir)
sys.path.insert(0, project_dir)

def validate_quick_setup():
    """Validación rápida de la configuración"""
    
    print("🧪 VALIDACIÓN RÁPIDA - INTEGRACIÓN GEMINI API")
    print("=" * 50)
    
    # 1. Verificar variables de entorno
    print("\n1️⃣  Verificando variables de entorno...")
    
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        print(f"   ✅ API Key encontrada (longitud: {len(gemini_key)})")
    else:
        print("   ❌ No se encontró GEMINI_API_KEY o GOOGLE_API_KEY")
        print("   💡 Configura: export GEMINI_API_KEY=tu_clave_aqui")
        return False
    
    generative_enabled = os.getenv('GENERATIVE_ENABLED', 'false').lower()
    print(f"   📋 GENERATIVE_ENABLED: {generative_enabled}")
    
    confidence_threshold = os.getenv('CONFIDENCE_THRESHOLD', '0.85')
    print(f"   📋 CONFIDENCE_THRESHOLD: {confidence_threshold}")
    
    # 2. Verificar importaciones
    print("\n2️⃣  Verificando importaciones...")
    
    try:
        import google.generativeai as genai
        print("   ✅ google-generativeai importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando google-generativeai: {e}")
        print("   💡 Instala: pip install google-generativeai")
        return False
    
    try:
        from generative.gemini_api_manager import GeminiAPIManager
        print("   ✅ GeminiAPIManager importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando GeminiAPIManager: {e}")
        return False
    
    try:
        from generative.generative_route import GenerativeRoute
        print("   ✅ GenerativeRoute importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando GenerativeRoute: {e}")
        return False
    
    try:
        from generative.router_central import RouterCentral
        print("   ✅ RouterCentral importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando RouterCentral: {e}")
        return False
    
    # 3. Test básico de conexión
    print("\n3️⃣  Probando conexión con Gemini...")
    
    try:
        manager = GeminiAPIManager()
        if not manager.is_available():
            print("   ⚠️  GeminiAPIManager no está disponible")
            print("   💡 Verifica tu API key y configuración")
            return False
        
        # Test de conexión simple
        test_result = manager.test_connection()
        if test_result['success']:
            print(f"   ✅ Conexión exitosa!")
            print(f"   📱 Modelo: {test_result.get('model', 'unknown')}")
            print(f"   ⏱️  Tiempo: {test_result.get('response_time', 0):.2f}s")
            print(f"   💬 Respuesta: \"{test_result.get('test_response', '')}\"")
        else:
            print(f"   ❌ Conexión falló: {test_result.get('error', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en test de conexión: {str(e)}")
        return False
    
    # 4. Test de GenerativeRoute
    print("\n4️⃣  Probando GenerativeRoute...")
    
    try:
        route = GenerativeRoute()
        if route.is_available():
            test_result = route.test_functionality()
            if test_result['success']:
                print("   ✅ GenerativeRoute funcionando correctamente")
                print(f"   💬 Test: \"{test_result.get('test_query', '')}\"")
                print(f"   🤖 Respuesta: \"{test_result.get('response', '')}\"")
            else:
                print(f"   ❌ GenerativeRoute falló: {test_result.get('error', 'unknown')}")
                return False
        else:
            print("   ⚠️  GenerativeRoute no disponible (probablemente GENERATIVE_ENABLED=false)")
            print("   💡 Para activar: export GENERATIVE_ENABLED=true")
            
    except Exception as e:
        print(f"   ❌ Error en GenerativeRoute: {str(e)}")
        return False
    
    # 5. Test de RouterCentral
    print("\n5️⃣  Probando RouterCentral integrado...")
    
    try:
        # Mock intent manager simple
        class SimpleIntentManager:
            def classify_intent(self, text):
                return {'intent': 'test', 'confidence': 0.5, 'response': 'Test response'}
            def process_intent(self, text):
                return self.classify_intent(text)
        
        router = RouterCentral(SimpleIntentManager())
        
        # Test con consulta que debería ir a generativa (si está habilitada)
        test_query = "¿Cuál es tu color favorito?"
        result = router.process_user_input(test_query)
        
        if result['success']:
            print(f"   ✅ RouterCentral funcionando correctamente")
            print(f"   🛣️  Ruta elegida: {result.get('route', 'unknown')}")
            print(f"   💬 Respuesta: \"{result.get('response', '')[:50]}...\"")
            print(f"   📊 Confianza: {result.get('confidence', 0)}")
        else:
            print(f"   ❌ RouterCentral falló: {result.get('error', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en RouterCentral: {str(e)}")
        return False
    
    # ✅ Todo funcionando
    print("\n" + "=" * 50)
    print("🎉 ¡VALIDACIÓN EXITOSA!")
    print("\n📋 Resumen:")
    print("   ✅ Variables de entorno configuradas")
    print("   ✅ Módulos importados correctamente")
    print("   ✅ Conexión con Gemini API funcionando")
    print("   ✅ GenerativeRoute operativa")
    print("   ✅ RouterCentral integrado")
    
    print("\n🚀 Próximos pasos:")
    print("   1. Configura GENERATIVE_ENABLED=true para activar IA generativa")
    print("   2. Integra RouterCentral en improved_app.py")
    print("   3. Ejecuta tests completos: python3 modules/generative/test_connection.py")
    
    return True

def show_configuration_example():
    """Muestra ejemplo de configuración"""
    print("\n📝 CONFIGURACIÓN RECOMENDADA:")
    print("   export GEMINI_API_KEY=tu_clave_gemini_aqui")
    print("   export GENERATIVE_ENABLED=true")
    print("   export CONFIDENCE_THRESHOLD=0.85")
    print("   export GEMINI_MODEL=gemini-1.5-pro")
    print("   export GEMINI_TIMEOUT=30")

def main():
    """Función principal"""
    print("Iniciando validación rápida del setup de Gemini...")
    
    if validate_quick_setup():
        print("\n✅ El sistema está listo para usar con IA generativa!")
    else:
        print("\n❌ Hay problemas en la configuración.")
        show_configuration_example()
        print("\n💡 Revisa los errores y ejecuta nuevamente este script.")
        sys.exit(1)

if __name__ == "__main__":
    main()