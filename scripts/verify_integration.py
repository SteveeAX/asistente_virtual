#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de verificación para la integración de IA generativa
Verifica que todo funciona correctamente sin romper el sistema existente

Autor: Asistente Kata
Fecha: 2024-08-16
Versión: 1.0.0
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")

def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

class IntegrationVerifier:
    """Verificador de la integración de IA generativa"""
    
    def __init__(self):
        self.project_dir = "/home/steveen/asistente_kata"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def run_verification(self):
        """Ejecuta todas las verificaciones"""
        print_header("VERIFICACIÓN INTEGRACIÓN IA GENERATIVA")
        
        # Cambiar al directorio del proyecto
        os.chdir(self.project_dir)
        
        # Lista de verificaciones
        verifications = [
            ("Estructura de Directorios", self.verify_directory_structure),
            ("Archivos de Configuración", self.verify_config_files),
            ("Dependencias Python", self.verify_dependencies),
            ("RouterCentral", self.verify_router_central),
            ("Configuración Usuario", self.verify_user_preferences),
            ("Sistema Clásico", self.verify_classic_system),
            ("Integración Completa", self.verify_full_integration),
            ("Logs y Métricas", self.verify_logging),
        ]
        
        for test_name, test_func in verifications:
            self.run_test(test_name, test_func)
        
        self.print_summary()
        self.save_results()
    
    def run_test(self, test_name: str, test_func):
        """Ejecuta una verificación individual"""
        print(f"\n{Colors.BOLD}Verificando: {test_name}{Colors.END}")
        self.results['summary']['total'] += 1
        
        try:
            result = test_func()
            if result['status'] == 'success':
                print_success(result['message'])
                self.results['summary']['passed'] += 1
            elif result['status'] == 'warning':
                print_warning(result['message'])
                self.results['summary']['warnings'] += 1
            else:
                print_error(result['message'])
                self.results['summary']['failed'] += 1
            
            self.results['tests'].append({
                'name': test_name,
                'status': result['status'],
                'message': result['message'],
                'details': result.get('details', [])
            })
            
        except Exception as e:
            error_msg = f"Error ejecutando verificación: {str(e)}"
            print_error(error_msg)
            self.results['summary']['failed'] += 1
            self.results['tests'].append({
                'name': test_name,
                'status': 'error',
                'message': error_msg,
                'traceback': traceback.format_exc()
            })
    
    def verify_directory_structure(self) -> Dict[str, Any]:
        """Verifica que la estructura de directorios esté creada"""
        required_dirs = [
            'src/ai/generative',
            'config/generative',
            'data/preferences',
            'logs/generative',
            'scripts'
        ]
        
        missing_dirs = []
        existing_dirs = []
        
        for dir_path in required_dirs:
            full_path = os.path.join(self.project_dir, dir_path)
            if os.path.exists(full_path) and os.path.isdir(full_path):
                existing_dirs.append(dir_path)
            else:
                missing_dirs.append(dir_path)
        
        if not missing_dirs:
            return {
                'status': 'success',
                'message': f'Todos los directorios creados ({len(existing_dirs)}/{len(required_dirs)})',
                'details': existing_dirs
            }
        else:
            return {
                'status': 'error',
                'message': f'Faltan directorios: {", ".join(missing_dirs)}',
                'details': {'missing': missing_dirs, 'existing': existing_dirs}
            }
    
    def verify_config_files(self) -> Dict[str, Any]:
        """Verifica que los archivos de configuración existan"""
        required_files = [
            'requirements_generative.txt',
            '.env.template',
            'data/preferences/user_preferences.json',
            'scripts/backup_sistema.sh',
            'scripts/install_generative.sh',
            'GUIA_INTEGRACION_IA_GENERATIVA.md'
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in required_files:
            full_path = os.path.join(self.project_dir, file_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        if not missing_files:
            return {
                'status': 'success',
                'message': f'Todos los archivos de configuración presentes ({len(existing_files)}/{len(required_files)})',
                'details': existing_files
            }
        else:
            return {
                'status': 'error',
                'message': f'Faltan archivos: {", ".join(missing_files)}',
                'details': {'missing': missing_files, 'existing': existing_files}
            }
    
    def verify_dependencies(self) -> Dict[str, Any]:
        """Verifica que las dependencias críticas estén instaladas"""
        critical_deps = [
            'json',  # stdlib
            'os',    # stdlib
            'logging',  # stdlib
            'datetime'  # stdlib
        ]
        
        optional_deps = [
            'openai',
            'google.generativeai',
            'aiohttp',
            'dotenv'
        ]
        
        missing_critical = []
        missing_optional = []
        
        # Verificar dependencias críticas
        for dep in critical_deps:
            try:
                __import__(dep)
            except ImportError:
                missing_critical.append(dep)
        
        # Verificar dependencias opcionales
        for dep in optional_deps:
            try:
                if dep == 'google.generativeai':
                    import google.generativeai
                elif dep == 'dotenv':
                    from dotenv import load_dotenv
                else:
                    __import__(dep)
            except ImportError:
                missing_optional.append(dep)
        
        if missing_critical:
            return {
                'status': 'error',
                'message': f'Faltan dependencias críticas: {", ".join(missing_critical)}',
                'details': {'critical_missing': missing_critical, 'optional_missing': missing_optional}
            }
        elif missing_optional:
            return {
                'status': 'warning',
                'message': f'Dependencias opcionales faltantes: {", ".join(missing_optional)} (necesarias para IA generativa)',
                'details': {'optional_missing': missing_optional}
            }
        else:
            return {
                'status': 'success',
                'message': 'Todas las dependencias están disponibles',
                'details': {'all_available': critical_deps + optional_deps}
            }
    
    def verify_router_central(self) -> Dict[str, Any]:
        """Verifica que RouterCentral se pueda importar y funcione"""
        try:
            # Agregar el directorio src al path si no está
            src_path = os.path.join(self.project_dir, 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            # Intentar importar RouterCentral
            from ai.generative.router_central import RouterCentral
            
            # Crear un mock intent manager simple para testing
            class MockIntentManager:
                def classify_intent(self, text):
                    return {
                        'intent': 'test_intent',
                        'confidence': 0.8,
                        'response': 'Test response',
                        'entities': {}
                    }
                
                def process_intent(self, text):
                    return self.classify_intent(text)
            
            # Crear instancia del router
            mock_intent_manager = MockIntentManager()
            router = RouterCentral(mock_intent_manager)
            
            # Test básico de funcionalidad
            test_input = "¿qué hora es?"
            result = router.process_user_input(test_input)
            
            # Verificar que el resultado tenga la estructura esperada
            expected_keys = ['success', 'route', 'response']
            missing_keys = [key for key in expected_keys if key not in result]
            
            if missing_keys:
                return {
                    'status': 'error',
                    'message': f'RouterCentral no retorna estructura esperada. Faltan: {missing_keys}',
                    'details': {'result': result}
                }
            
            # Verificar estadísticas
            stats = router.get_stats()
            
            return {
                'status': 'success',
                'message': 'RouterCentral funciona correctamente',
                'details': {
                    'test_result': result,
                    'stats': stats,
                    'generative_enabled': router.generative_enabled
                }
            }
            
        except ImportError as e:
            return {
                'status': 'error',
                'message': f'No se puede importar RouterCentral: {str(e)}',
                'details': {'import_error': str(e)}
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error probando RouterCentral: {str(e)}',
                'details': {'error': str(e), 'traceback': traceback.format_exc()}
            }
    
    def verify_user_preferences(self) -> Dict[str, Any]:
        """Verifica que las preferencias de usuario sean válidas"""
        try:
            preferences_path = os.path.join(self.project_dir, 'data/preferences/user_preferences.json')
            
            with open(preferences_path, 'r', encoding='utf-8') as f:
                preferences = json.load(f)
            
            # Verificar estructura básica
            required_sections = ['ia_generativa', 'comandos_clasicos', 'usuario', 'asistente']
            missing_sections = [section for section in required_sections if section not in preferences]
            
            if missing_sections:
                return {
                    'status': 'error',
                    'message': f'Faltan secciones en user_preferences.json: {missing_sections}',
                    'details': {'missing': missing_sections}
                }
            
            # Verificar configuración IA generativa
            ia_config = preferences.get('ia_generativa', {})
            if 'habilitada' not in ia_config:
                return {
                    'status': 'warning',
                    'message': 'Configuración de IA generativa incompleta',
                    'details': {'ia_config': ia_config}
                }
            
            return {
                'status': 'success',
                'message': f'Preferencias válidas (IA generativa: {"habilitada" if ia_config.get("habilitada") else "deshabilitada"})',
                'details': {
                    'sections': list(preferences.keys()),
                    'ia_enabled': ia_config.get('habilitada', False),
                    'classic_confidence': ia_config.get('confianza_minima_clasica', 'not_set')
                }
            }
            
        except FileNotFoundError:
            return {
                'status': 'error',
                'message': 'Archivo user_preferences.json no encontrado',
                'details': {'path': preferences_path}
            }
        except json.JSONDecodeError as e:
            return {
                'status': 'error',
                'message': f'Error en formato JSON de user_preferences.json: {str(e)}',
                'details': {'json_error': str(e)}
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error verificando preferencias: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def verify_classic_system(self) -> Dict[str, Any]:
        """Verifica que el sistema clásico siga funcionando"""
        try:
            # Intentar importar módulos del sistema clásico
            classic_modules = ['intent_manager', 'tts_manager', 'stt_manager']
            available_modules = []
            missing_modules = []
            
            for module in classic_modules:
                try:
                    __import__(module)
                    available_modules.append(module)
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                return {
                    'status': 'warning',
                    'message': f'Algunos módulos clásicos no disponibles: {missing_modules}',
                    'details': {'available': available_modules, 'missing': missing_modules}
                }
            else:
                return {
                    'status': 'success',
                    'message': f'Sistema clásico disponible ({len(available_modules)} módulos)',
                    'details': {'available_modules': available_modules}
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error verificando sistema clásico: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def verify_full_integration(self) -> Dict[str, Any]:
        """Verifica la integración completa simulando el flujo real"""
        try:
            # Simular integración completa
            src_path = os.path.join(self.project_dir, 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            from ai.generative.router_central import RouterCentral
            
            # Verificar que se puede crear y usar sin el intent_manager real
            class DummyIntentManager:
                def classify_intent(self, text):
                    return {'intent': 'dummy', 'confidence': 0.5, 'response': 'dummy response'}
                def process_intent(self, text):
                    return self.classify_intent(text)
            
            dummy_manager = DummyIntentManager()
            router = RouterCentral(dummy_manager)
            
            # Probar varios casos de uso
            test_cases = [
                "¿qué hora es?",
                "recordatorio medicación",
                "emergencia",
                "pregunta compleja sobre la vida"
            ]
            
            results = []
            for test_case in test_cases:
                result = router.process_user_input(test_case)
                results.append({
                    'input': test_case,
                    'route': result.get('route'),
                    'success': result.get('success', False)
                })
            
            successful_tests = [r for r in results if r['success']]
            
            if len(successful_tests) == len(test_cases):
                return {
                    'status': 'success',
                    'message': f'Integración completa exitosa ({len(successful_tests)}/{len(test_cases)} tests)',
                    'details': {'test_results': results}
                }
            else:
                return {
                    'status': 'warning',
                    'message': f'Integración parcial ({len(successful_tests)}/{len(test_cases)} tests exitosos)',
                    'details': {'test_results': results}
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error en integración completa: {str(e)}',
                'details': {'error': str(e), 'traceback': traceback.format_exc()}
            }
    
    def verify_logging(self) -> Dict[str, Any]:
        """Verifica que el sistema de logging funcione"""
        try:
            log_dir = os.path.join(self.project_dir, 'logs/generative')
            
            if not os.path.exists(log_dir):
                return {
                    'status': 'warning',
                    'message': 'Directorio de logs no existe (se creará automáticamente)',
                    'details': {'log_dir': log_dir}
                }
            
            # Verificar permisos de escritura
            test_file = os.path.join(log_dir, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
                return {
                    'status': 'success',
                    'message': 'Sistema de logging configurado correctamente',
                    'details': {'log_dir': log_dir, 'writable': True}
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'No se puede escribir en directorio de logs: {str(e)}',
                    'details': {'log_dir': log_dir, 'error': str(e)}
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error verificando logging: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def print_summary(self):
        """Imprime el resumen de resultados"""
        print_header("RESUMEN DE VERIFICACIÓN")
        
        total = self.results['summary']['total']
        passed = self.results['summary']['passed']
        failed = self.results['summary']['failed']
        warnings = self.results['summary']['warnings']
        
        print(f"\n{Colors.BOLD}Resultados:{Colors.END}")
        print_success(f"Exitosas: {passed}/{total}")
        if warnings > 0:
            print_warning(f"Advertencias: {warnings}/{total}")
        if failed > 0:
            print_error(f"Fallidas: {failed}/{total}")
        
        if failed == 0:
            if warnings == 0:
                print_success("\n🎉 ¡VERIFICACIÓN COMPLETAMENTE EXITOSA!")
                print_info("El sistema está listo para usar con RouterCentral")
            else:
                print_warning("\n⚠️  VERIFICACIÓN EXITOSA CON ADVERTENCIAS")
                print_info("El sistema funcionará, pero revisa las advertencias")
        else:
            print_error("\n❌ VERIFICACIÓN FALLÓ")
            print_info("Revisa los errores antes de continuar")
        
        # Próximos pasos
        print(f"\n{Colors.BOLD}Próximos pasos:{Colors.END}")
        if failed == 0:
            print_info("1. Seguir la guía de integración: GUIA_INTEGRACION_IA_GENERATIVA.md")
            print_info("2. Configurar API keys en .env si planeas usar IA generativa")
            print_info("3. Integrar RouterCentral en improved_app.py")
        else:
            print_info("1. Resolver los errores reportados")
            print_info("2. Ejecutar nuevamente este script de verificación")
            print_info("3. Consultar los logs para más detalles")
    
    def save_results(self):
        """Guarda los resultados en un archivo"""
        try:
            results_file = os.path.join(self.project_dir, 'logs/generative/verification_results.json')
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print_info(f"\nResultados guardados en: {results_file}")
            
        except Exception as e:
            print_warning(f"No se pudieron guardar los resultados: {str(e)}")

def main():
    """Función principal"""
    print_info(f"Iniciando verificación en: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    verifier = IntegrationVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main()