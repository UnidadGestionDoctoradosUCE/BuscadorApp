"""
Sistema de Cache Inteligente para Documentos
Evita re-escanner documentos que no han cambiado
"""
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Imports del proyecto
from services.file_service import cargar_documentos
import config.settings as settings
from utils.text_utils import normalizar_texto


class CacheInteligente:
    """
    Cache que evita re-escannear documentos no modificados
    """
    
    def __init__(self, archivo_cache="cache_documentos.json"):
        """Inicializa el cache"""
        # directorio del usuario
        app_data = os.path.expanduser("~/.buscadorapp")
        os.makedirs(app_data, exist_ok=True)
        
        self.ruta_cache = os.path.join(app_data, archivo_cache)
        self.cache = self._cargar_cache()
    
    def _cargar_cache(self):
        """Carga el cache desde archivo JSON"""
        if os.path.exists(self.ruta_cache):
            try:
                with open(self.ruta_cache, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"documentos": [], "ultimo_escaneo": None}
        return {"documentos": [], "ultimo_escaneo": None}
    
    def _guardar_cache(self):
        """Guarda el cache a archivo JSON"""
        try:
            with open(self.ruta_cache, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARN] No se pudo guardar cache: {e}")
    
    def necesita_escaneo(self):
        """Determina si necesita escanear"""
        # Si no hay cache, necesita escanear
        if not self.cache.get("documentos"):
            return True
        
        # Si las rutas cambiaron, necesita escanear
        if (settings.ruta_doctorados != self.cache.get("ruta_doctorados") or
            settings.ruta_doctorados2 != self.cache.get("ruta_doctorados2")):
            return True

        # Validación de directorios por mtime
        ultimo_escaneo_str = self.cache.get("ultimo_escaneo")
        if ultimo_escaneo_str:
            try:
                ultimo_escaneo_dt = datetime.strptime(ultimo_escaneo_str, "%Y-%m-%d %H:%M:%S")
                for r in [settings.ruta_doctorados, settings.ruta_doctorados2]:
                    if r and os.path.exists(r):
                        dir_mtime = os.path.getmtime(r)
                        dir_dt = datetime.fromtimestamp(dir_mtime)
                        if dir_dt > ultimo_escaneo_dt:
                            print(f"[CACHE] Directorio {r} fue modificado después del último escaneo.")
                            return True
            except Exception as e:
                print(f"[CACHE] Error al validar mtime de directorio: {e}")
                return True
        
        # Validación de esquema (backward compatibility check)
        docs = self.cache.get("documentos", [])
        for doc in docs:
            if not isinstance(doc, dict):
                return True
            # Comprobamos que existan los campos normalizados
            for campo in ["nombre_norm", "universidad_norm", "programa_norm", "estudiante_norm", "item_clave"]:
                if campo not in doc:
                    print(f"[CACHE] Campo '{campo}' faltante en cache. Se requiere re-escaneo.")
                    return True
        
        return False
    
    def obtener_documentos(self):
        """
        Retorna documentos: del cache o escaneandolos si es necesario
        Retorna: (documentos, fue_desde_cache)
        """
        # Si ya tiene documentos en settings y no necesita escaneo, usarlos
        if settings.documentos_drive and not self.necesita_escaneo():
            return settings.documentos_drive, True
        
        # Si el cache en disco es válido, cargarlo directamente a settings
        if not self.necesita_escaneo():
            print("[CACHE] Cargando documentos desde el cache en disco en O(1)...")
            settings.documentos_drive = self.cache.get("documentos", [])
            settings.documentos_cargados = True
            return settings.documentos_drive, True
        
        # Necesita escanear
        return None, False
    
    def escanear_con_cache(self, progress_callback=None):
        """
        Escanea documentos usando cache inteligente
        Retorna cantidad de docs nuevos vs cacheados
        """
        print("[CACHE] Iniciando escaneo inteligente...")
    
        documentos_cache = {doc["ruta"]: doc for doc in self.cache.get("documentos", [])}
        nuevos_documentos = []
        documentos_encontrados = 0
        desde_cache = 0
        
        # Rutas a escanear
        rutas = []
        if settings.ruta_doctorados:
            rutas.append(settings.ruta_doctorados)
        if settings.ruta_doctorados2:
            rutas.append(settings.ruta_doctorados2)
        
        if not rutas:
            return []
        
        print(f"[CACHE] Rutas a escanear: {rutas}")
        print(f"[CACHE] Documentos en cache anterior: {len(documentos_cache)}")
        
        for ruta_base in rutas:
            if not os.path.exists(ruta_base):
                print(f"[CACHE] Ruta no existe: {ruta_base}")
                continue
            
            print(f"[CACHE] Escaneando: {ruta_base}")
            
            for root, dirs, files in os.walk(ruta_base):
                for file in files:
                    if not file.lower().endswith('.pdf'):
                        continue
                    
                    ruta_completa = os.path.join(root, file)
                    
                    # Obtener fecha de modificación
                    try:
                        fecha_mod = os.path.getmtime(ruta_completa)
                        fecha_str = datetime.fromtimestamp(fecha_mod).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Verificar si ya está en cache y no cambió
                    if ruta_completa in documentos_cache:
                        doc_cache = documentos_cache[ruta_completa]
                        if doc_cache.get("fecha_mod") == fecha_str:
                            # No cambió, usar del cache
                            nuevos_documentos.append(doc_cache)
                            desde_cache += 1
                            continue
                    
                    # El archivo cambió o es nuevo, procesarlo
                    doc = self._procesar_documento(ruta_completa, file)
                    if doc:
                        nuevos_documentos.append(doc)
                    
                    documentos_encontrados += 1
                    
                    if progress_callback and documentos_encontrados % 100 == 0:
                        print(f"[CACHE] Procesados: {documentos_encontrados}...")
        
        # Resumen
        print(f"[CACHE] === RESUMEN ===")
        print(f"[CACHE] Total documentos: {len(nuevos_documentos)}")
        print(f"[CACHE] Desde cache (sin cambiar): {desde_cache}")
        print(f"[CACHE] Nuevos/modificados: {len(nuevos_documentos) - desde_cache}")
        
        # Guardar cache
        self.cache = {
            "documentos": nuevos_documentos,
            "ultimo_escaneo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ruta_doctorados": settings.ruta_doctorados,
            "ruta_doctorados2": settings.ruta_doctorados2
        }
        self._guardar_cache()
        
        print(f"[CACHE] Cache guardado en: {self.ruta_cache}")
        
        return nuevos_documentos
    
    def _procesar_documento(self, ruta, nombre_archivo):
        """Procesa un documento individual"""
        try:
            # Extraer información del path
            partes = ruta.split(os.sep)
            num_partes = len(partes)
            
            # Estructura típica: 
            # .../Universidad/NombreUniv/Programa/Estudiante/Archivo.pdf (sin subcarpeta)
            # O:
            # .../Universidad/NombreUniv/Programa/Estudiante/TipoDoc/Archivo.pdf (con subcarpeta)
            
            # La carpeta inmediata (sin .pdf) = ultima carpeta del path
            carpeta_inmediata = partes[-2] if num_partes >= 2 else ""
            
            # Si es una palabra o dos, es tipo de documento (Pre-requisitos, Tesis, etc)
            # Entonces el estudiante está 1 nivel más arriba
            palabras_carpeta = carpeta_inmediata.split()
            
            if len(palabras_carpeta) <= 2 and carpeta_inmediata:
                # Hay subcarpeta tipo: estudiante en -3
                # Ejs: "Pre-requisitos", "Tesis", "Correspondencia"
                estudiante = partes[-3] if num_partes >= 3 else nombre_archivo
                programa = partes[-4] if num_partes >= 4 else "Unknown"
                universidad = partes[-5] if num_partes >= 5 else "Unknown"
            else:
                # Sin subcarpeta: estudiante en -2
                estudiante = partes[-2] if num_partes >= 2 else nombre_archivo
                programa = partes[-3] if num_partes >= 3 else "Unknown"
                universidad = partes[-4] if num_partes >= 4 else "Unknown"
            
            # Limpiar nombre del documento
            nombre_limpio = nombre_archivo.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
            nombre_norm = normalizar_texto(nombre_limpio)
            
            # Clasificación de ítem clave usando aliases de settings
            item_clave_detectado = None
            if hasattr(settings, 'items_clave') and settings.items_clave:
                for item_clave, alias_list in settings.items_clave.items():
                    if any(normalizar_texto(alias) in nombre_norm for alias in alias_list):
                        item_clave_detectado = item_clave
                        break

            # Obtener fecha
            try:
                fecha_mod = os.path.getmtime(ruta)
                fecha_str = datetime.fromtimestamp(fecha_mod).strftime("%Y-%m-%d %H:%M:%S")
            except:
                fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                "ruta": ruta,
                "nombre": nombre_limpio,
                "nombre_norm": nombre_norm,
                "universidad": universidad,
                "universidad_norm": normalizar_texto(universidad),
                "programa": programa,
                "programa_norm": normalizar_texto(programa),
                "estudiante": estudiante,
                "estudiante_norm": normalizar_texto(estudiante),
                "item_clave": item_clave_detectado,
                "fecha_mod": fecha_str
            }
        except Exception as e:
            print(f"[WARN] Error procesando {ruta}: {e}")
            return None
    
    def invalidate(self):
        """Invalida el cache (fuerza re-escaneo)"""
        self.cache = {"documentos": [], "ultimo_escaneo": None}
        self._guardar_cache()
        print("[CACHE] Cache invalidado")


# Instancia global del cache
_cache = None

def get_cache():
    """Retorna la instancia global del cache"""
    global _cache
    if _cache is None:
        print("[CACHE] Creando nueva instancia de CacheInteligente")
        _cache = CacheInteligente()
    return _cache


def usar_cache_inteligente(progress_callback=None):
    """Función principal: usa el cache inteligente para obtener documentos"""
    cache = get_cache()
    
    print(f"[CACHE] Estado: {cache.cache.get('ultimo_escaneo', 'NUNCA')}")
    
    # Intentar obtener de cache
    docs, fue_desde_cache = cache.obtener_documentos()
    if fue_desde_cache:
        print(f"[CACHE] Usando docs de cache. Escaneo omitido. Total docs: {len(docs)}")
        return docs
    
    # Escannear
    docs = cache.escanear_con_cache(progress_callback)
    settings.documentos_drive = docs
    settings.documentos_cargados = True
    return docs