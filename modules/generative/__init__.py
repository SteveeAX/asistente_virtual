# Módulo de IA generativa para Asistente Kata
# Autor: Asistente Kata
# Versión: 1.0.0

"""
Módulo de capacidades de IA generativa que extiende
las funcionalidades clásicas del asistente sin reemplazarlas.

Componentes principales:
- RouterCentral: Enrutamiento inteligente entre sistemas clásico y generativo
- GenerativeManager: Gestión de múltiples proveedores de IA
- ContextManager: Manejo de contexto y memoria conversacional
- SecurityFilter: Filtros de seguridad y contenido
"""

__version__ = "1.0.0"
__author__ = "Asistente Kata"

from .router_central import RouterCentral
from .gemini_api_manager import GeminiAPIManager  
from .generative_route import GenerativeRoute

__all__ = ['RouterCentral', 'GeminiAPIManager', 'GenerativeRoute']