"""
Utilidades para procesamiento de texto
"""
import unicodedata


def normalizar_texto(texto):
    """
    Normaliza texto para búsquedas con tolerancia a caracteres especiales.
    - Convierte a minúsculas
    - Elimina tildes y diacríticos
    - Ejemplos: "María" -> "maria", "PeñA" -> "penA", "ñoño" -> "nono"
    
    Args:
        texto: Texto a normalizar
    Returns:
        str: Texto normalizado (sin tildes, en minúsculas)
    """
    if not texto:
        return ""
    
    # Normalizar a forma NFD (descompone caracteres con diacríticos)
    # Ej: "á" -> "a" + marca combinante
    normalized = unicodedata.normalize('NFD', texto.lower())
    
    # Filtrar caracteres diacríticos (marcas de combinación Unicode)
    # Estos son los caracteres que aparecen después de una letra normal
    return ''.join(c for c in normalized if not unicodedata.combining(c))


def texto_contiene(texto, busqueda):
    """
    Verifica si un texto contiene una búsqueda, ignorando tildes y mayúsculas.
    
    Args:
        texto: Texto donde buscar
        busqueda: Texto a buscar
    Returns:
        bool: True si contiene, False si no
    """
    texto_norm = normalizar_texto(texto)
    busqueda_norm = normalizar_texto(busqueda)
    return busqueda_norm in texto_norm


def texto_empieza_con(texto, prefijo):
    """
    Verifica si un texto empieza con un prefijo, ignorando tildes y mayúsculas.
    
    Args:
        texto: Texto a verificar
        prefijo: Prefijo a buscar
    Returns:
        bool: True si empieza con el prefijo, False si no
    """
    texto_norm = normalizar_texto(texto)
    prefijo_norm = normalizar_texto(prefijo)
    return texto_norm.startswith(prefijo_norm)


import difflib

def coincidencia_difusa(texto, busqueda, umbral=0.65):
    """
    Verifica si hay una coincidencia aproximada/difusa entre el texto y la búsqueda.
    Usa normalizar_texto para ignorar mayúsculas y tildes.
    - Fast path: si la búsqueda exacta está contenida en el texto, retorna True.
    - Fallback: calcula la similitud usando difflib.SequenceMatcher de forma global y por palabras.
    """
    if not busqueda:
        return True
    if not texto:
        return False
        
    texto_norm = normalizar_texto(texto)
    busqueda_norm = normalizar_texto(busqueda)
    
    # 1. Validación estricta de números si existen en la búsqueda.
    # Evita que '001' coincida con '0019' o '1001' por subcadena o SequenceMatcher.
    import re
    nums_busqueda = re.findall(r'\d+', busqueda_norm)
    if nums_busqueda:
        nums_texto = re.findall(r'\d+', texto_norm)
        for nb in nums_busqueda:
            val_b = nb.lstrip('0') or '0'
            matched = False
            for nt in nums_texto:
                val_t = nt.lstrip('0') or '0'
                if val_b == val_t:
                    matched = True
                    break
            if not matched:
                return False  # Si algún número de la búsqueda no coincide exactamente en valor en el texto, descartamos
    
    # Fast path: coincidencia de subcadena exacta
    if busqueda_norm in texto_norm:
        return True
        
    # Fallback 1: Ratio de similitud directo (solo si NO contiene números para evitar falsos positivos como 100 vs 600)
    if not nums_busqueda:
        matcher = difflib.SequenceMatcher(None, texto_norm, busqueda_norm)
        if matcher.ratio() >= umbral:
            return True
        
    # Fallback 2: Coincidencia palabra por palabra (para búsquedas multi-término)
    palabras_busqueda = busqueda_norm.split()
    palabras_texto = texto_norm.split()
    
    if not palabras_busqueda or not palabras_texto:
        return False
        
    coincidencias_palabras = 0
    for p_b in palabras_busqueda:
        encontrado = False
        es_numero_b = any(c.isdigit() for c in p_b)
        for p_t in palabras_texto:
            if p_b in p_t:
                encontrado = True
                break
            # Similitud difusa en la palabra: solo si NO contiene números
            if not es_numero_b and len(p_t) >= 3 and len(p_b) >= 3:
                ratio = difflib.SequenceMatcher(None, p_t, p_b).ratio()
                if ratio >= umbral:
                    encontrado = True
                    break
        if encontrado:
            coincidencias_palabras += 1
            
    # Si todas las palabras de la búsqueda tienen un match difuso en el texto
    return coincidencias_palabras == len(palabras_busqueda)

