# BuscadorApp — Sistema de Gestión Documental (UCE)

Aplicación de escritorio nativa para Windows desarrollada en **Python + Flet (Flutter Desktop)** para la búsqueda, consulta y descarga de expedientes de **Doctorados** y **Oficios** de la Universidad Central del Ecuador.

Cuenta con diseño **Glassmorphism**, transiciones fluidas (`AnimatedSwitcher`), **modo Claro / Oscuro dinámico con persistencia**, diseño **100% responsive** para cualquier tamaño de pantalla, caché local inteligente y empaquetado en ejecutable `.exe` autocontenido.

---

## 1. Estructura del Proyecto

```text
BuscadorApp/
├── main.py                      # Punto de entrada principal, navegación, responsive y tema dinámico
├── compilar_flet.bat            # Script rápido para compilar el ejecutable AppBuscador.exe
├── requirements.txt             # Dependencias de Python del proyecto
├── README.md                    # Documentación única de desarrollo, compilación y mantenimiento
├── config/
│   ├── __init__.py
│   └── settings.py              # Estado global, glosario items_clave y persistencia de rutas/tema
├── data/
│   ├── cifrador.py              # CLI para registrar o actualizar usuarios con SHA-256
│   └── usuarios.json            # Base de usuarios autorizados (credenciales cifradas)
├── imagenes/
│   ├── logouce.png              # Logo principal e ícono de la aplicación
│   └── logouce3.png             # Emblema para Splash Screen y estado inicial
├── services/
│   ├── __init__.py
│   ├── cache_service.py         # Caché inteligente (~/.buscadorapp/cache_documentos.json)
│   ├── file_service.py          # Escaneo físico de PDFs y clasificación por glosario
│   └── search_service.py        # Búsqueda difusa tolerante a tildes y filtros dependientes
├── ui_flet/
│   ├── __init__.py
│   ├── services_bridge.py       # Puente de lógica (auth SHA-256, abrir PDFs, crear ZIPs)
│   ├── theme.py                 # Paletas Claro/Oscuro, Glassmorphism, diálogos y helpers UI
│   ├── components/
│   │   ├── __init__.py
│   │   └── config_dialog.py     # Modal de configuración de rutas Drive y apariencia
│   └── views/
│       ├── __init__.py
│       ├── splash_view.py       # Pantalla inicial con detección automática de Drive
│       ├── login_view.py        # Inicio de sesión institucional
│       ├── loading_view.py      # Bienvenida post-login y precalentamiento del caché
│       ├── selection_view.py    # Panel ejecutivo con KPIs y selector de módulos
│       ├── docentes_view.py     # Módulo de Doctorados (tabla izquierda + filtros derecha)
│       ├── oficios_view.py      # Módulo de Oficios (filtros izquierda + tabla derecha)
│       └── acerca_de_view.py    # Información técnica y créditos
└── utils/
    ├── __init__.py
    ├── file_utils.py            # resource_path() compatible con PyInstaller y estructura oficios
    ├── path_utils.py            # Auto-detección de carpetas de Google Drive en unidades locales
    └── text_utils.py            # Normalización de texto y coincidencia difusa
```

---

## 2. Requisitos Previos e Instalación (Desarrollo)

- **Sistema Operativo:** Windows 10 u 11 (64 bits).
- **Python:** 3.10 – 3.13 (probado con **Python 3.13.4**).

Instala las dependencias desde la raíz del proyecto:

```powershell
python -m pip install -r requirements.txt
```

*(Opcional recomendado)*: trabajar dentro de un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

---

## 3. Ejecución en Modo Desarrollo

Desde la raíz del proyecto:

```powershell
python main.py
```

---

## 4. Creación del Ejecutable (`.exe`) y Distribución

### Opción A: Usando el script automático
Haz doble clic o ejecuta en PowerShell:

```powershell
.\compilar_flet.bat
```

### Opción B: Comando manual
```powershell
flet pack main.py --name "AppBuscador" --icon "imagenes\logouce.png" --add-data "imagenes;imagenes" --add-data "data;data" -y
```

El ejecutable final se genera en:

```text
dist\AppBuscador.exe
```

### Cómo distribuirlo en otras computadoras
1. Copia únicamente el archivo **`dist\AppBuscador.exe`** a las computadoras destino (no requiere Python instalado ni librerías adicionales).
2. Al abrirlo por primera vez, el sistema detecta automáticamente las unidades montadas de Google Drive (`G:\Mi unidad\...`, `H:\Mi unidad\...`, etc.).
3. Si en una máquina la ruta es distinta, abre **Ajustes** (desde la pantalla de Selección) y utiliza **Examinar** o **Auto-detectar Drive**.

> **Nota sobre rutas empaquetadas:** El archivo `data\usuarios.json` e `imagenes\` quedan incrustados dentro del `.exe` y se leen mediante `utils.file_utils.resource_path(...)`. La configuración editable por el usuario y el caché se guardan en el perfil de Windows para persistir entre ejecuciones.

---

## 5. Guía de Mantenimiento y Actualización para Futuras Versiones

### 5.1. Agregar o actualizar usuarios de acceso
Los usuarios están almacenados con hash SHA-256 en `data/usuarios.json`. Nunca edites los hashes a mano; utiliza el asistente CLI incluido:

```powershell
python data/cifrador.py
```

Introduce el nombre completo, el nombre de usuario y la contraseña. Si el usuario ya existe, actualiza su contraseña y nombre sin afectar a los demás registros. Luego **recompila el `.exe`** para que el nuevo `usuarios.json` quede incluido.

### 5.2. Agregar nuevos ítems clave o tipos de documentos
En `config/settings.py`, edita el diccionario `items_clave`:

```python
items_clave = {
    ...
    "30. Nuevo Documento": ["palabraclave1", "palabraclave2"],
}
```

> **Importante:** Cada vez que agregues un nuevo ítem clave o modifiques aliases, el usuario debe pulsar **"Sincronizar Documentos"** dentro del módulo de Docentes para reconstruir el caché con la nueva clasificación.

### 5.3. Personalizar colores, tema Claro/Oscuro o estilo Glassmorphism
Todo el sistema visual está centralizado en `ui_flet/theme.py`:
- `LIGHT_PALETTE` y `DARK_PALETTE`: definen fondos, bordes, encabezados de tabla, acentos y opacidades glass.
- `crear_glass_card(...)`: controla el desenfoque (`blur_sigma`) y sombras de las tarjetas.
- `crear_fondo_ambiental(...)`: controla el gradiente base y los orbes ambientales.

### 5.4. Dónde se guardan los datos persistentes en cada máquina
- **En modo ejecutable (`.exe`):** `%USERPROFILE%\.buscadorapp\settings.json` (rutas de Drive y tema `"light"` / `"dark"`).
- **En modo desarrollo (`python main.py`):** `data\settings.json`.
- **Caché de documentos indexados:** `%USERPROFILE%\.buscadorapp\cache_documentos.json`.

### 5.5. Cómo crear nuevas pantallas o modificar vistas
1. Todas las vistas viven en `ui_flet/views/` e implementan `build()`, `on_mount()` y `dispose()` (para cancelar timers o hilos de fondo).
2. Si deseas que la vista responda a cambios de tamaño de ventana, implementa `on_resize(self, width, height, update_ui=True)` — `AppFlet` en `main.py` lo invoca automáticamente con debounce.
3. Si deseas que el cambio de tema Claro/Oscuro en vivo conserve los filtros o búsqueda de la vista, implementa `get_state()` y `restore_state(state)`.
4. Usa `ui_flet/services_bridge.py` o `services/` para toda la lógica; **nunca importes `tkinter`** en ninguna capa.
5. Para publicar una nueva versión:
   - Actualiza el número de versión en `ui_flet/views/acerca_de_view.py`, `splash_view.py` y `login_view.py`.
   - Ejecuta las comprobaciones de sintaxis (`python -m py_compile main.py ...`).
   - Ejecuta `compilar_flet.bat` y prueba el archivo resultante `dist\AppBuscador.exe` antes de distribuirlo.

---

## 6. Solución Rápida de Problemas

- **Drive aparece como "Drive Desconectado":** Verifica que **Google Drive para escritorio** esté abierto e iniciado sesión en Windows, o configura manualmente las carpetas desde **Ajustes**.
- **Los documentos recién subidos a Drive no aparecen:** Haz clic en el botón verde **Sincronizar Documentos** para invalidar el caché y re-escanear las carpetas.
- **No se ven cambios tras modificar `usuarios.json` en el `.exe`:** Recuerda ejecutar `compilar_flet.bat` nuevamente después de editar archivos dentro de `data/` o `imagenes/`.
- **Error `flet` no reconocido al compilar:** Ejecuta `python -m flet.cli pack ...` o asegúrate de tener activo el entorno de Python donde instalaste `requirements.txt`.
