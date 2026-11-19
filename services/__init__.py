"""
Paquete de servicios para AppBuscador.

Contiene la lógica de negocio de la aplicación (libre de dependencias de interfaz):
- Escaneo e indexación de documentos y oficios
- Sistema de caché inteligente
- Búsqueda y filtrado de datos
"""

from .file_service import (
    cargar_documentos,
    cargar_documentos_oficios,
    resolver_item_clave_fisico,
)
from .search_service import (
    buscar_documentos,
    buscar_oficios,
    obtener_estudiantes_filtrados,
    obtener_items_clave_filtrados,
    obtener_programas_filtrados,
    obtener_tipos_oficios_filtrados,
)

__all__ = [
    "resolver_item_clave_fisico",
    "cargar_documentos",
    "cargar_documentos_oficios",
    "buscar_documentos",
    "buscar_oficios",
    "obtener_programas_filtrados",
    "obtener_estudiantes_filtrados",
    "obtener_items_clave_filtrados",
    "obtener_tipos_oficios_filtrados",
]
