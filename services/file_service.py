"""
Servicio de escaneo y clasificación física de archivos PDF desde Google Drive.
"""
import os
import config.settings as settings
from utils.text_utils import normalizar_texto


def resolver_item_clave_fisico(nombre_doc):
    """Auxiliar para resolver el ítem clave durante el escaneo en disco."""
    nombre_doc_norm = normalizar_texto(nombre_doc)
    for item_clave, alias_list in settings.items_clave.items():
        if any(normalizar_texto(alias) in nombre_doc_norm for alias in alias_list):
            return item_clave
    return None


def cargar_documentos(ruta, progress_callback=None):
    """Carga todos los documentos PDF de una ruta dada de doctorados."""
    if not ruta:
        return []

    documentos = []
    for carpeta, _, archivos in os.walk(ruta):
        if progress_callback:
            carpeta_relativa = os.path.relpath(carpeta, ruta)
            progress_callback(carpeta_relativa, len(documentos))

        for archivo in archivos:
            if archivo.lower().endswith(".pdf"):
                ruta_completa = os.path.join(carpeta, archivo)
                nombre_archivo = archivo.replace(".pdf", "").replace("_", " ").lower()

                partes_ruta = os.path.relpath(ruta_completa, ruta).split(os.sep)
                universidad = partes_ruta[0] if len(partes_ruta) > 0 else ""
                programa = partes_ruta[1] if len(partes_ruta) > 1 else ""
                estudiante = partes_ruta[2] if len(partes_ruta) > 2 else ""

                documentos.append({
                    "universidad": universidad,
                    "universidad_norm": normalizar_texto(universidad),
                    "programa": programa,
                    "programa_norm": normalizar_texto(programa),
                    "estudiante": estudiante,
                    "estudiante_norm": normalizar_texto(estudiante),
                    "nombre": nombre_archivo,
                    "nombre_norm": normalizar_texto(nombre_archivo),
                    "ruta": ruta_completa,
                    "item_clave": resolver_item_clave_fisico(nombre_archivo),
                })

    return documentos


def cargar_documentos_oficios(ruta, progress_callback=None):
    """Carga todos los oficios PDF de una ruta dada."""
    if not ruta:
        return []

    documentos = []
    for carpeta, _, archivos in os.walk(ruta):
        if progress_callback:
            carpeta_relativa = os.path.relpath(carpeta, ruta)
            progress_callback(carpeta_relativa, len(documentos))

        for archivo in archivos:
            if archivo.lower().endswith(".pdf"):
                ruta_completa = os.path.join(carpeta, archivo)
                partes_ruta = os.path.relpath(ruta_completa, ruta).split(os.sep)

                if len(partes_ruta) >= 4:
                    anio = partes_ruta[0]
                    periodo = partes_ruta[1]
                    tipo = partes_ruta[2]
                else:
                    anio = periodo = tipo = ""

                nombre_archivo = archivo.replace(".pdf", "").replace("_", " ").lower()
                documentos.append({
                    "anio": anio,
                    "periodo": periodo,
                    "tipo": tipo,
                    "nombre": nombre_archivo,
                    "ruta": ruta_completa,
                })

    return documentos
