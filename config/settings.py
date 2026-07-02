"""
Configuración global de la aplicación
Contiene constantes, rutas y variables de estado global
"""
import os
import json

# Ruta del archivo de configuración
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "settings.json")

# Tema global de la aplicación (light / dark)
theme = "light"

# Variables globales de estado
documentos_drive = []
ruta_por_iid = {}
nombre_usuario_actual = ""

# Variables globales de UI
logo_img_global = None
login_logo_img_global = None

# Rutas de Drive (se inicializan al arrancar)
ruta_doctorados = None
ruta_oficios = None
ruta_doctorados2 = None

# Diccionario de items clave para clasificación de documentos
items_clave = {
    "1. Hoja de Vida": ["h.vida"],
    "2. Contrato de Beca": ["c.beca"],
    "3. Contrato de Licencia": ["c.licencia"],
    "4. Aval de Facultad": ["avalfacultad"],
    "5. Acción Personal": ["acciónpersonal"],
    "6. Datos del Garante": ["d.garante"],
    "7. Cédula y Papeleta de Votación": ["cédulaypapeleta"],
    "8. Pasaporte": ["pasaporte"],
    "9. Declaración Juramentada": ["declaraciónjuramentada"],
    "10. Solicitud de Pedido al Rectorado": ["solicitudpedidorectorado"],
    "11. Carta de Admisión de la Universidad": ["cartaadmisiónuniversidad"],
    "12. Certificado de Cuenta Bancaria": ["certificadobancario"],
    "13. Matrícula": ["matrícula"],
    "14. Certificado de Aprobación Tesis": ["certificadoaprobación"],
    "15. Reporte de Notas Semestrales": ["reportenotas"],
    "16. Línea de Investigación y Plan de Tesis": ["lineamientoinvestigacióntesis"],
    "17. Informe de Avance de Tesis Emitido por el Tutor": ["informeavance"],
    "18. Correspondencia": ["correspondencia"],
    "19. Registro de Títulos SENESCYT": ["registrosenescyt"],
    "20. Adenda": ["adenda"],
    "21. Oficios": ["oficio"],
    "22. Contrato IECE": ["c.iece"],
    "23. Contrato Senescyt": ["c.senescyt"],
    "24. Acta Finiquito": ["a.finiquito"],
    "25. Contrato apoyo financiero": ["c.apoyofinanciero"],
    "26. Contrato reducción carga horaria": ["c.reduccionhoraria"],
    "27. Documentos Precontractuales": ["DocumentosPrecontractuales"],
    "28. Extensión de Beca": ["extensionbeca"],
    "29. Certificado de Tesis": ["CertificadoTesis"]
}

# Variables globales para oficios
estructura_oficios = None
documentos_oficios = []
ruta_por_iid_oficios = {}

# Flags para evitar recargas innecesarias de documentos
documentos_cargados = False
oficios_cargados = False

# Lista de universidades
universidades_lista = []

def cargar_configuracion():
    global ruta_doctorados, ruta_oficios, ruta_doctorados2, theme
    theme = "light"
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                ruta_doctorados = config.get("ruta_doctorados", None)
                ruta_oficios = config.get("ruta_oficios", None)
                ruta_doctorados2 = config.get("ruta_doctorados2", None)
        except Exception as e:
            print(f"Error al cargar configuración: {e}")

def guardar_configuracion(r_doc, r_of, r_doc2, current_theme=None):
    global ruta_doctorados, ruta_oficios, ruta_doctorados2, theme
    ruta_doctorados = r_doc
    ruta_oficios = r_of
    ruta_doctorados2 = r_doc2
    theme = "light"
    
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    config = {
        "ruta_doctorados": ruta_doctorados,
        "ruta_oficios": ruta_oficios,
        "ruta_doctorados2": ruta_doctorados2
    }
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error al guardar configuración: {e}")

# Cargar configuración al importar el módulo
cargar_configuracion()

