"""
Puente de servicios para la interfaz Flet, 100% libre de dependencias de Tkinter.
Reutiliza la lógica central de config/, utils/ y services/ sin invocar messagebox ni filedialog.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from typing import Optional

import config.settings as settings
from utils.file_utils import resource_path


def verificar_credenciales_flet(usuario: str, contrasena: str) -> tuple[bool, Optional[str], str]:
    """
    Verifica las credenciales contra data/usuarios.json mediante SHA-256.
    Returns:
        tuple: (valido, nombre_real, mensaje_error)
    """
    ruta_json = resource_path("data/usuarios.json")
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            lista_usuarios = json.load(f)

        usuario_hash = hashlib.sha256(usuario.encode("utf-8")).hexdigest()
        contrasena_hash = hashlib.sha256(contrasena.encode("utf-8")).hexdigest()

        usuario_encontrado = None
        for u in lista_usuarios:
            if u.get("usuario") == usuario_hash:
                usuario_encontrado = u
                break

        if not usuario_encontrado:
            return False, None, "Este usuario no está registrado en el sistema."

        if usuario_encontrado.get("contrasena") == contrasena_hash:
            return True, usuario_encontrado.get("nombre", usuario), ""

        return False, None, "Usuario o contraseña incorrectos."
    except Exception as e:
        return False, None, f"No se pudo verificar credenciales: {e}"


def obtener_tipo_documento_flet(nombre_archivo: str) -> Optional[str]:
    """Obtiene el tipo limpio del documento según settings.items_clave."""
    if not nombre_archivo:
        return None
    nombre_lower = nombre_archivo.lower()
    for nombre_completo, aliases in settings.items_clave.items():
        for alias in aliases:
            if alias.lower() in nombre_lower:
                return nombre_completo.split(". ", 1)[-1]
    return None


def convertir_nombre_a_glosario_flet(nombre_archivo: str) -> str:
    """Convierte el nombre del archivo a su nombre completo del glosario o Title Case."""
    tipo = obtener_tipo_documento_flet(nombre_archivo)
    if tipo:
        return tipo
    return nombre_archivo.title() if nombre_archivo else ""


def limpiar_nombre_documento_docente(doc: dict) -> str:
    """Aplica el glosario y elimina el nombre del estudiante si aparece pegado al final."""
    nombre_doc = convertir_nombre_a_glosario_flet(doc.get("nombre", ""))
    estudiante_raw = (doc.get("estudiante") or "").strip()
    if not estudiante_raw:
        return nombre_doc

    est_lower = estudiante_raw.lower()
    if nombre_doc.lower().endswith(est_lower):
        return nombre_doc[: len(nombre_doc) - len(est_lower)].strip(" -_")

    est_compact = est_lower.replace(" ", "")
    if est_compact and nombre_doc.lower().replace(" ", "").endswith(est_compact):
        restantes = len(est_compact)
        idx = len(nombre_doc)
        while idx > 0 and restantes > 0:
            idx -= 1
            if nombre_doc[idx] != " ":
                restantes -= 1
        return nombre_doc[:idx].strip(" -_")

    return nombre_doc


def abrir_pdf_flet(ruta: str) -> tuple[bool, str]:
    """Abre un archivo PDF con la aplicación predeterminada del sistema operativo."""
    if not ruta or not os.path.exists(ruta):
        return False, f"El archivo no existe o Drive no está disponible:\n{ruta}"
    try:
        if os.name == "nt":
            os.startfile(ruta)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta])
        return True, ""
    except Exception as e:
        return False, f"No se pudo abrir el archivo: {e}"


def copiar_pdf_a_destino(ruta_origen: str, ruta_destino: str) -> tuple[bool, str]:
    """Copia un PDF hacia la ruta elegida por el usuario."""
    if not ruta_origen or not os.path.exists(ruta_origen):
        return False, "El archivo original no existe o no está accesible."
    try:
        if not ruta_destino.lower().endswith(".pdf"):
            ruta_destino = f"{ruta_destino}.pdf"
        shutil.copy2(ruta_origen, ruta_destino)
        return True, f"Archivo guardado en:\n{ruta_destino}"
    except Exception as e:
        return False, f"No se pudo descargar el archivo: {e}"


def _ruta_zip_unica(carpeta_destino: str, nombre_base: str) -> str:
    """Genera una ruta de archivo .zip sin sobrescribir archivos existentes."""
    ruta_zip = os.path.join(carpeta_destino, f"{nombre_base}.zip")
    contador = 1
    while os.path.exists(ruta_zip):
        ruta_zip = os.path.join(carpeta_destino, f"{nombre_base}_{contador}.zip")
        contador += 1
    return ruta_zip


def crear_zip_multiple(
    rutas_documentos: list[str],
    carpeta_destino: str,
    nombre_base: str = "Documentos_Filtrados",
) -> tuple[bool, str, int]:
    """
    Empaqueta múltiples PDFs en un archivo .zip manteniendo la carpeta padre para evitar colisiones.
    Returns:
        tuple: (exito, ruta_zip_o_mensaje_error, cantidad_archivos)
    """
    if not rutas_documentos:
        return False, "No hay documentos seleccionados para descargar.", 0
    if not carpeta_destino or not os.path.isdir(carpeta_destino):
        return False, "La carpeta de destino seleccionada no es válida.", 0

    ruta_zip = _ruta_zip_unica(carpeta_destino, nombre_base)
    archivos_agregados = 0
    try:
        with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            usados = set()
            for ruta_doc in rutas_documentos:
                if os.path.exists(ruta_doc) and os.path.isfile(ruta_doc):
                    nombre_archivo = os.path.basename(ruta_doc)
                    carpeta_padre = os.path.basename(os.path.dirname(ruta_doc))
                    nombre_en_zip = f"{carpeta_padre}/{nombre_archivo}" if carpeta_padre else nombre_archivo
                    if nombre_en_zip in usados:
                        base, ext = os.path.splitext(nombre_en_zip)
                        idx = 1
                        while f"{base}_{idx}{ext}" in usados:
                            idx += 1
                        nombre_en_zip = f"{base}_{idx}{ext}"
                    usados.add(nombre_en_zip)
                    zipf.write(ruta_doc, nombre_en_zip)
                    archivos_agregados += 1

        if archivos_agregados == 0:
            if os.path.exists(ruta_zip):
                os.remove(ruta_zip)
            return False, "No se encontraron archivos accesibles para comprimir.", 0

        return True, ruta_zip, archivos_agregados
    except Exception as e:
        if os.path.exists(ruta_zip):
            try:
                os.remove(ruta_zip)
            except Exception:
                pass
        return False, f"No se pudo crear el archivo ZIP: {e}", 0


def crear_zip_expediente(ruta_pdf: str, carpeta_destino: str) -> tuple[bool, str, int]:
    """
    Comprime toda la carpeta del estudiante (directorio padre del PDF) en un ZIP.
    Returns:
        tuple: (exito, ruta_zip_o_mensaje_error, cantidad_archivos)
    """
    if not ruta_pdf:
        return False, "Ruta de documento inválida.", 0
    if not carpeta_destino or not os.path.isdir(carpeta_destino):
        return False, "La carpeta de destino seleccionada no es válida.", 0

    carpeta_estudiante = os.path.dirname(ruta_pdf)
    if not os.path.isdir(carpeta_estudiante):
        return False, f"No se encontró la carpeta del expediente:\n{carpeta_estudiante}", 0

    nombre_estudiante = os.path.basename(carpeta_estudiante) or "Estudiante"
    ruta_zip = _ruta_zip_unica(carpeta_destino, f"Expediente_{nombre_estudiante}")
    archivos_agregados = 0

    try:
        with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for carpeta_actual, _, archivos in os.walk(carpeta_estudiante):
                for archivo in archivos:
                    ruta_completa = os.path.join(carpeta_actual, archivo)
                    ruta_relativa = os.path.relpath(ruta_completa, carpeta_estudiante)
                    zipf.write(ruta_completa, ruta_relativa)
                    archivos_agregados += 1

        if archivos_agregados == 0:
            if os.path.exists(ruta_zip):
                os.remove(ruta_zip)
            return False, "La carpeta del estudiante no contiene archivos.", 0

        return True, ruta_zip, archivos_agregados
    except Exception as e:
        if os.path.exists(ruta_zip):
            try:
                os.remove(ruta_zip)
            except Exception:
                pass
        return False, f"No se pudo crear el expediente: {e}", 0


def obtener_documentos_estudiante(doc: dict) -> list[dict]:
    """Obtiene todos los documentos del mismo estudiante en settings.documentos_drive."""
    if not doc or not settings.documentos_drive:
        return []
    univ = doc.get("universidad")
    prog = doc.get("programa")
    est = doc.get("estudiante")
    return [
        d
        for d in settings.documentos_drive
        if d.get("universidad") == univ
        and d.get("programa") == prog
        and d.get("estudiante") == est
    ]


def verificar_drive_conectado() -> bool:
    """Comprueba si al menos una de las rutas configuradas de Drive existe en disco."""
    for ruta in (settings.ruta_doctorados, settings.ruta_doctorados2, settings.ruta_oficios):
        if ruta and os.path.exists(ruta):
            return True
    return False
