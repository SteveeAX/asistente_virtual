# time_interpreter.py
import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def parse_natural_time(text: str) -> dict:
    """
    Interpreta expresiones de tiempo naturales en español para adultos mayores.
    
    Ejemplos:
    - "a las 3 de la tarde" → 15:00
    - "a las 8 de la mañana" → 08:00
    - "a las 10 de la noche" → 22:00
    - "al mediodía" → 12:00
    - "a medianoche" → 00:00
    - "mañana a las 3" → mañana 15:00 (asume tarde si no especifica)
    
    Retorna: {'hour': int, 'minute': int, 'day_offset': int, 'success': bool}
    """
    
    text = text.lower().strip()
    logger.info(f"TIME_PARSER: Interpretando '{text}'")
    
    result = {
        'hour': None,
        'minute': 0,
        'day_offset': 0,  # 0=hoy, 1=mañana, 2=pasado mañana
        'success': False
    }
    
    # 1. Detectar día relativo
    if 'mañana' in text and 'por la mañana' not in text and 'de la mañana' not in text:
        result['day_offset'] = 1
        logger.info("TIME_PARSER: Detectado 'mañana' (día siguiente)")
    elif 'pasado mañana' in text:
        result['day_offset'] = 2
        logger.info("TIME_PARSER: Detectado 'pasado mañana'")
    
    # 2. Casos especiales de tiempo
    special_times = {
        'mediodía': (12, 0),
        'medianoche': (0, 0),
        'medio día': (12, 0),
        'media noche': (0, 0),
        'al mediodía': (12, 0),
        'a medianoche': (0, 0)
    }
    
    for phrase, (hour, minute) in special_times.items():
        if phrase in text:
            result['hour'] = hour
            result['minute'] = minute
            result['success'] = True
            logger.info(f"TIME_PARSER: Tiempo especial detectado: {hour:02d}:{minute:02d}")
            return result
    
    # 3. Buscar patrones de hora con período del día
    
    # Patrón principal: "a las X (y Y) (de la/por la) (mañana/tarde/noche)"
    hour_patterns = [
        # Con minutos y período: "a las 4 y 45 de la tarde"
        r'a las (\d{1,2})\s*y\s*(\d{1,2})\s*(?:de la|por la)?\s*(mañana|tarde|noche)',
        # Con minutos formato : y período: "a las 4:45 de la tarde"  
        r'a las (\d{1,2}):(\d{1,2})\s*(?:de la|por la)?\s*(mañana|tarde|noche)',
        # Sin minutos pero con período: "a las 3 de la tarde"
        r'a las (\d{1,2})\s*(?:de la|por la)?\s*(mañana|tarde|noche)',
        # Formato 24h puro: "a las 15:30" o "a las 15"
        r'a las (\d{1,2}):(\d{2})',
        r'a las (\d{1,2})\s*(?:horas?)?$'
    ]
    
    for i, pattern in enumerate(hour_patterns):
        match = re.search(pattern, text)
        if match:
            if i == 0:  # Con minutos y período (y)
                hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3)
                result['hour'] = _convert_to_24h(hour, period)
                result['minute'] = minute
            elif i == 1:  # Con minutos formato : y período
                hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3)
                result['hour'] = _convert_to_24h(hour, period)
                result['minute'] = minute
            elif i == 2:  # Sin minutos pero con período
                hour, period = int(match.group(1)), match.group(2)
                result['hour'] = _convert_to_24h(hour, period)
                result['minute'] = 0
            elif i == 3:  # Formato 24h con minutos
                result['hour'] = int(match.group(1))
                result['minute'] = int(match.group(2))
            elif i == 4:  # Formato 24h sin minutos
                hour = int(match.group(1))
                # Si es hora ambigua (1-12), asumir tarde si es entre 1-7, mañana si es 8-12
                if hour <= 12:
                    if hour >= 1 and hour <= 7:
                        result['hour'] = hour + 12  # Asumir tarde
                        logger.info(f"TIME_PARSER: Hora ambigua {hour}, asumiendo tarde: {hour + 12}:00")
                    else:
                        result['hour'] = hour if hour == 12 else hour  # Mantener como está
                else:
                    result['hour'] = hour
                result['minute'] = 0
            
            result['success'] = True
            logger.info(f"TIME_PARSER: Patrón {i+1} detectado: {result['hour']:02d}:{result['minute']:02d}")
            break
    
    # 4. Validar resultado
    if result['success']:
        if result['hour'] is None or result['hour'] < 0 or result['hour'] > 23:
            result['success'] = False
            logger.warning(f"TIME_PARSER: Hora inválida: {result['hour']}")
        elif result['minute'] < 0 or result['minute'] > 59:
            result['success'] = False
            logger.warning(f"TIME_PARSER: Minuto inválido: {result['minute']}")
    
    if result['success']:
        logger.info(f"TIME_PARSER: ✅ Resultado final: {result['hour']:02d}:{result['minute']:02d} (día +{result['day_offset']})")
    else:
        logger.warning(f"TIME_PARSER: ❌ No se pudo interpretar el tiempo en '{text}'")
    
    return result

def _convert_to_24h(hour: int, period: str) -> int:
    """Convierte hora de 12h a 24h según el período del día."""
    
    if period == 'mañana':
        if hour == 12:
            return 0  # 12 de la mañana = medianoche
        else:
            return hour  # 1-11 de la mañana
    
    elif period == 'tarde':
        if hour == 12:
            return 12  # 12 de la tarde = mediodía
        else:
            return hour + 12  # 1-11 de la tarde = 13-23
    
    elif period == 'noche':
        if hour == 12:
            return 0  # 12 de la noche = medianoche
        else:
            return hour + 12 if hour <= 11 else hour  # 1-11 de la noche = 13-23
    
    return hour  # Fallback

def format_time_confirmation(hour: int, minute: int, day_offset: int = 0) -> str:
    """Formatea el tiempo para confirmación en lenguaje natural."""
    
    # Determinar período del día
    if hour == 0:
        period = "medianoche"
        display_hour = 12
    elif hour < 12:
        period = "de la mañana"
        display_hour = hour if hour != 0 else 12
    elif hour == 12:
        period = "del mediodía"
        display_hour = 12
    elif hour < 19:
        period = "de la tarde"
        display_hour = hour - 12
    else:
        period = "de la noche"
        display_hour = hour - 12
    
    # Formatear tiempo
    if minute == 0:
        time_str = f"las {display_hour} {period}"
    else:
        time_str = f"las {display_hour}:{minute:02d} {period}"
    
    # Añadir día si no es hoy
    if day_offset == 0:
        day_str = "hoy"
    elif day_offset == 1:
        day_str = "mañana"
    elif day_offset == 2:
        day_str = "pasado mañana"
    else:
        day_str = f"en {day_offset} días"
    
    return f"{day_str} a {time_str}"

def calculate_reminder_datetime(hour: int, minute: int, day_offset: int = 0) -> dict:
    """Calcula el datetime exacto para el recordatorio. Retorna dict con validación."""
    
    base_date = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Si es para hoy pero la hora ya pasó, NO permitir
    if day_offset == 0 and base_date <= datetime.now():
        logger.warning(f"TIME_PARSER: Hora {hour:02d}:{minute:02d} ya pasó hoy")
        return {
            'success': False,
            'error': 'time_passed',
            'datetime': None,
            'message': f"Esa hora ya pasó. Di 'mañana a las {hour:02d}:{minute:02d}' si quieres el recordatorio para mañana."
        }
    
    target_date = base_date + timedelta(days=day_offset)
    return {
        'success': True,
        'error': None,
        'datetime': target_date,
        'message': None
    }

# Función de testing
def test_time_parser():
    """Prueba el parser con diferentes entradas."""
    test_cases = [
        "a las 3 de la tarde",
        "a las 8 de la mañana", 
        "a las 10 de la noche",
        "al mediodía",
        "a medianoche",
        "mañana a las 2 de la tarde",
        "a las 15:30",
        "a las 7",
        "pasado mañana a las 9 de la mañana",
        "a las 12 y 30 de la tarde"
    ]
    
    print("=== PRUEBAS DEL PARSER DE TIEMPO ===")
    for text in test_cases:
        result = parse_natural_time(text)
        if result['success']:
            formatted = format_time_confirmation(result['hour'], result['minute'], result['day_offset'])
            target_dt = calculate_reminder_datetime(result['hour'], result['minute'], result['day_offset'])
            print(f"✅ '{text}' → {formatted} ({target_dt.strftime('%Y-%m-%d %H:%M')})")
        else:
            print(f"❌ '{text}' → No interpretado")

if __name__ == "__main__":
    test_time_parser()
