"""
Servicio de búsqueda de documentos y oficios
"""
from tkinter import messagebox
import config.settings as settings
from utils.text_utils import normalizar_texto, texto_contiene, coincidencia_difusa


def buscar_documentos(filtro_u, filtro_p, filtro_e, filtro_nombre, filtro_item):
    """
    Busca documentos de forma ultra veloz en memoria.
    Aprovecha al 100% los campos pre-normalizados del caché.
    """
    encontrados = []

    # Verificar que haya documentos cargados
    if not settings.documentos_drive:
        print("[WARN] buscar_documentos: documentos_drive está vacío")
        return []

    # 1. Normalizar filtros de entrada UNA sola vez fuera del bucle
    filtro_u_norm = normalizar_texto(filtro_u) if filtro_u and filtro_u != '(Todos)' else None
    filtro_p_norm = normalizar_texto(filtro_p) if filtro_p and filtro_p != '(Todos)' else None
    filtro_e_norm = normalizar_texto(filtro_e) if filtro_e and filtro_e != '(Todos)' else None
    filtro_item_activo = filtro_item if filtro_item and filtro_item != '(Todos)' else None

    # 2. Bucle de complejidad reducida con cortocircuitos tempranos
    try:
        for d in settings.documentos_drive:
            # Universidad
            if filtro_u_norm and d.get('universidad_norm') != filtro_u_norm:
                continue
                
            # Programa
            if filtro_p_norm and d.get('programa_norm') != filtro_p_norm:
                continue
                
            # Estudiante
            if filtro_e_norm and d.get('estudiante_norm') != filtro_e_norm:
                continue
                
            # Nombre de Documento (Coincidencia Difusa)
            if filtro_nombre:
                en_nombre = coincidencia_difusa(d.get('nombre', ''), filtro_nombre)
                en_estudiante = coincidencia_difusa(d.get('estudiante', ''), filtro_nombre)
                if not en_nombre and not en_estudiante:
                    continue
                
            # Ítem Clave - Resolución O(1) limpia
            if filtro_item_activo and d.get('item_clave') != filtro_item_activo:
                continue

            encontrados.append(d)
    except Exception as e:
        print(f"[ERROR] buscar_documentos: {e}")

    return encontrados


def buscar_oficios(filtro_anio, filtro_tipo, filtro_nombre):
    """
    Busca oficios según los filtros aplicados.
    Las búsquedas son tolerantes a tildes, mayúsculas/minúsculas y eñes.
    
    Args:
        filtro_anio: Filtro de año
        filtro_tipo: Filtro de tipo de oficio
        filtro_nombre: Filtro de nombre de oficio
    Returns:
        list: Lista de oficios encontrados
    """
    docs = settings.documentos_oficios
    
    if filtro_anio != '(Todos)':
        docs = [doc for doc in docs if doc['anio'] == filtro_anio]
    
    if filtro_tipo != '(Todos)':
        docs = [doc for doc in docs if normalizar_texto(doc['tipo']) == normalizar_texto(filtro_tipo)]
    
    if filtro_nombre:
        docs = [doc for doc in docs if coincidencia_difusa(doc['nombre'], filtro_nombre)]
    
    return docs


def obtener_programas_filtrados(universidad):
    """
    Obtiene programas filtrados por universidad
    Args:
        universidad: Nombre de la universidad o '(Todos)'
    Returns:
        list: Lista ordenada de programas
    """
    if not settings.documentos_drive:
        return []

    if universidad == '(Todos)':
        programas = sorted(set(doc['programa'] for doc in settings.documentos_drive))
    else:
        programas = sorted(set(doc['programa'] for doc in settings.documentos_drive
                             if doc['universidad'] == universidad))
    return programas


def obtener_estudiantes_filtrados(universidad, programa):
    """
    Obtiene estudiantes filtrados por universidad y programa
    Args:
        universidad: Nombre de la universidad o '(Todos)'
        programa: Nombre del programa o '(Todos)'
    Returns:
        list: Lista ordenada de estudiantes
    """
    if not settings.documentos_drive:
        return []

    estudiantes = set()
    for doc in settings.documentos_drive:
        if (universidad == '(Todos)' or doc['universidad'] == universidad) and \
           (programa == '(Todos)' or doc['programa'] == programa):
            estudiantes.add(doc['estudiante'])
    return sorted(estudiantes)


def obtener_items_clave_filtrados(universidad, programa, estudiante):
    """
    Obtiene ítems clave filtrados de forma optimizada
    """
    if estudiante == '(Todos)':
        return sorted(settings.items_clave.keys())
    
    # Filtrar documentos del estudiante
    documentos_estudiante = []
    for doc in settings.documentos_drive:
        if (universidad == '(Todos)' or doc['universidad'] == universidad) and \
           (programa == '(Todos)' or doc['programa'] == programa) and \
           doc['estudiante'] == estudiante:
            documentos_estudiante.append(doc)
    
    # Encontrar qué ítems clave tiene el estudiante en O(1) por doc
    items_encontrados = set()
    for doc in documentos_estudiante:
        item = doc.get('item_clave')
        if item:
            items_encontrados.add(item)
    
    return sorted(items_encontrados)


def obtener_tipos_oficios_filtrados(anio, estructura_oficios):
    """
    Obtiene tipos de oficios filtrados por año
    Args:
        anio: Año seleccionado o '(Todos)'
        estructura_oficios: Estructura de oficios
    Returns:
        list: Lista ordenada de tipos de oficios
    """
    tipos = set()
    if estructura_oficios:
        if anio != '(Todos)':
            for tipos_periodo in estructura_oficios.get(anio, {}).values():
                tipos.update(tipos_periodo)
        else:
            for anio_val in estructura_oficios.values():
                for tipos_periodo in anio_val.values():
                    tipos.update(tipos_periodo)
    return sorted(tipos)

