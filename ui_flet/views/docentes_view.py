"""
Vista del módulo de Docentes en Flet con Glassmorphism, modo Claro/Oscuro dinámico y preservación de estado.
Mantiene fielmente la distribución original: contenido principal a la izquierda y sidebar de filtros a la derecha.
"""
import threading
import time
from typing import Callable, Optional
import flet as ft

import config.settings as settings
from services.cache_service import get_cache
from services.search_service import (
    buscar_documentos,
    obtener_estudiantes_filtrados,
    obtener_items_clave_filtrados,
    obtener_programas_filtrados,
)
from ui_flet.services_bridge import (
    abrir_pdf_flet,
    crear_zip_expediente,
    limpiar_nombre_documento_docente,
    obtener_documentos_estudiante,
    obtener_tipo_documento_flet,
)
from ui_flet.theme import (
    DriveMonitor,
    FilePickerHelper,
    actualizar_badge_drive,
    actualizar_dropdown_opciones,
    anim_fast,
    anim_smooth,
    crear_avatar_iniciales,
    crear_badge_drive,
    crear_boton_tema,
    crear_chip_filtro_activo,
    crear_dropdown_filtro,
    crear_fondo_ambiental,
    crear_glass_card,
    crear_paginador,
    get_palette,
    get_viewport_size,
    iniciar_descarga_archivos,
    normalizar_valor_dropdown,
    show_confirm_dialog,
    show_info_dialog,
    show_snackbar,
)
from utils.file_utils import resource_path
from utils.path_utils import encontrar_rutas_drive, obtener_todas_universidades_combinadas

PAGE_SIZE = 100

COLORES_TIPOS = {
    "Matrícula": "#10B981",
    "Cédula": "#3B82F6",
    "Acción de Personal": "#8B5CF6",
    "Certificado": "#F59E0B",
    "Título": "#EF4444",
    "Diploma": "#EC4899",
    "Pensum": "#6366F1",
    "Homologación": "#14B8A6",
}


class DocentesView:
    """Vista moderna del módulo de Docentes con distribución fiel a la original."""

    def __init__(
        self,
        page: ft.Page,
        file_picker: FilePickerHelper,
        on_volver: Callable[[], None],
        on_cerrar_sesion: Callable[[], None],
        on_toggle_theme: Optional[Callable[[], None]] = None,
    ):
        self.page = page
        self.file_picker = file_picker
        self.on_volver = on_volver
        self.on_cerrar_sesion = on_cerrar_sesion
        self.on_toggle_theme = on_toggle_theme

        self._activo = True
        self.search_seq = 0
        self._search_timer: Optional[threading.Timer] = None
        self._drive_monitor: Optional[DriveMonitor] = None

        self.resultados_totales: list[dict] = []
        self.pagina_actual = 0
        self.selected_paths: set[str] = set()
        self.focused_doc: Optional[dict] = None
        self.mostrar_col_doc = True
        self._last_click_ruta: str = ""
        self._last_click_ts: float = 0.0
        self._sidebar_manual_hidden: bool = False
        self._last_vp_width: float = 1280.0

        # Controles UI
        self.sidebar: ft.Container
        self.sidebar_logo_col: ft.Column
        self.btn_filtrar: ft.ElevatedButton
        self.btn_limpiar: ft.OutlinedButton
        self.main_content: ft.Container
        self.placeholder_logo: ft.Image
        self.btn_toggle_filtros: ft.OutlinedButton
        self.combo_universidad: ft.Dropdown
        self.combo_programa: ft.Dropdown
        self.combo_estudiante: ft.Dropdown
        self.combo_item_clave: ft.Dropdown
        self.entrada_busqueda: ft.TextField
        self.btn_clear_search: ft.IconButton
        self.pill_shortcut: ft.Container
        self.row_chips_filtros: ft.Row

        self.btn_sincronizar: ft.ElevatedButton
        self.badge_filtros_count: ft.Container
        self.lbl_filtros_count: ft.Text

        self.chip_seleccionados: ft.Container
        self.lbl_seleccionados: ft.Text
        self.chk_todos: ft.Checkbox
        self.col_header_doc: ft.Container
        self.lista_resultados: ft.ListView

        self.panel_placeholder: ft.Container
        self.panel_spinner: ft.Container
        self.lbl_spinner: ft.Text
        self.panel_tabla: ft.Container
        self.paginador: ft.Container
        self.lbl_pagina: ft.Text
        self.btn_prev_pag: ft.IconButton
        self.btn_next_pag: ft.IconButton

        self.lbl_status: ft.Text
        self.badge_drive: ft.Container
        self.icon_drive: ft.Icon
        self.txt_drive: ft.Text

    def dispose(self):
        self._activo = False
        if self._search_timer:
            try:
                self._search_timer.cancel()
            except Exception:
                pass
            self._search_timer = None
        if self._drive_monitor:
            self._drive_monitor.stop()
            self._drive_monitor = None

    def get_state(self) -> dict:
        return {
            "search_text": self.entrada_busqueda.value or "",
            "universidad": normalizar_valor_dropdown(self.combo_universidad.value),
            "programa": normalizar_valor_dropdown(self.combo_programa.value),
            "estudiante": normalizar_valor_dropdown(self.combo_estudiante.value),
            "item_clave": normalizar_valor_dropdown(self.combo_item_clave.value),
            "resultados": list(self.resultados_totales),
            "mostrar_col_doc": self.mostrar_col_doc,
            "pagina_actual": self.pagina_actual,
            "selected_paths": set(self.selected_paths),
            "focused_doc": self.focused_doc,
            "status_text": self.lbl_status.value or "Listo",
            "showing_table": self.panel_tabla.visible,
        }

    def restore_state(self, state: dict):
        if not state:
            return
        self._inicializar_filtros(update_ui=False)
        u = state.get("universidad", "(Todos)")
        p_val = state.get("programa", "(Todos)")
        e_val = state.get("estudiante", "(Todos)")
        item_val = state.get("item_clave", "(Todos)")

        actualizar_dropdown_opciones(
            self.combo_universidad,
            [o.key for o in self.combo_universidad.options] or ["(Todos)"],
            u,
            update_control=False,
        )
        programas = obtener_programas_filtrados(u)
        actualizar_dropdown_opciones(
            self.combo_programa, ["(Todos)"] + programas, p_val, update_control=False
        )
        estudiantes = obtener_estudiantes_filtrados(u, p_val)
        actualizar_dropdown_opciones(
            self.combo_estudiante, ["(Todos)"] + estudiantes, e_val, update_control=False
        )
        items = obtener_items_clave_filtrados(u, p_val, e_val)
        actualizar_dropdown_opciones(
            self.combo_item_clave, ["(Todos)"] + items, item_val, update_control=False
        )

        texto = state.get("search_text", "")
        self.entrada_busqueda.value = texto
        self.btn_clear_search.visible = bool(texto.strip())
        self.pill_shortcut.visible = not bool(texto.strip())
        self._actualizar_chips_filtros(update_ui=False)

        if state.get("showing_table") and state.get("resultados"):
            self.resultados_totales = list(state["resultados"])
            self.pagina_actual = state.get("pagina_actual", 0)
            self.selected_paths = set(state.get("selected_paths", set()))
            self.focused_doc = state.get("focused_doc")
            self.mostrar_col_doc = state.get("mostrar_col_doc", True)
            self.col_header_doc.visible = self.mostrar_col_doc
            self._activar_panel("tabla")
            self._renderizar_pagina()
        else:
            self._activar_panel("placeholder")

        self.lbl_status.value = state.get("status_text", "Listo")
        self._safe_update()

    def _safe_update(self, control: Optional[ft.Control] = None):
        if not self._activo:
            return
        try:
            if control is not None:
                control.update()
            else:
                self.page.update()
        except Exception:
            pass

    def build(self) -> ft.Control:
        p = get_palette()
        self.page.title = "Buscador de Doctorados - Docentes"
        btn_primary_fg = "#0B1120" if p["is_dark"] else ft.Colors.WHITE
        chip_fg = p["primary"] if p["is_dark"] else p["primary_dark"]

        # ------------------------------------------------------------------
        # 1. CONTENIDO PRINCIPAL (IZQUIERDA)
        # ------------------------------------------------------------------
        self.lbl_seleccionados = ft.Text(
            "", size=12, weight=ft.FontWeight.W_600, color=chip_fg
        )
        self.chip_seleccionados = ft.Container(
            visible=False,
            opacity=0.0,
            scale=0.9,
            animate_opacity=anim_fast(160),
            animate_scale=anim_fast(160),
            bgcolor=p["primary_soft"],
            border=ft.border.all(1, ft.Colors.with_opacity(0.35, p["primary"])),
            border_radius=16,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            content=self.lbl_seleccionados,
        )

        self.btn_toggle_filtros = ft.OutlinedButton(
            text="Filtros",
            icon=ft.Icons.TUNE_ROUNDED,
            visible=False,
            tooltip="Mostrar u ocultar panel de filtros",
            style=ft.ButtonStyle(
                color=p["primary"],
                side=ft.BorderSide(1, p["primary"]),
                bgcolor=p["surface_alt"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
            ),
            on_click=lambda _: self._toggle_sidebar_filtros(),
        )

        toolbar = crear_glass_card(
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            blur_sigma=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color=p["glass_shadow"],
                offset=ft.Offset(0, 4),
            ),
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        "BUSCADOR DE DOCTORADOS",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=p["text_primary"],
                                    ),
                                    self.chip_seleccionados,
                                ],
                                spacing=12,
                                wrap=True,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                "Gestión de expedientes académicos y programas",
                                size=12,
                                color=p["text_secondary"],
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Row(
                        [
                            self.btn_toggle_filtros,
                            ft.ElevatedButton(
                                text="Abrir",
                                icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                                bgcolor="#334155" if p["is_dark"] else "#475569",
                                color=ft.Colors.WHITE,
                                tooltip="Abrir PDF seleccionado o marcados",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                ),
                                on_click=lambda _: self.abrir_pdf_handler(),
                            ),
                            ft.ElevatedButton(
                                text="Descargar",
                                icon=ft.Icons.DOWNLOAD_ROUNDED,
                                bgcolor=p["primary"],
                                color=btn_primary_fg,
                                tooltip="Descargar PDF o paquete ZIP de marcados",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                ),
                                on_click=lambda _: self.descargar_seleccionados(),
                            ),
                            ft.OutlinedButton(
                                text="Expediente",
                                icon=ft.Icons.ARCHIVE_OUTLINED,
                                tooltip="Descargar carpeta completa del estudiante seleccionado",
                                style=ft.ButtonStyle(
                                    color=p["text_primary"],
                                    side=ft.BorderSide(1, p["border"]),
                                    bgcolor=p["surface_alt"],
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                ),
                                on_click=lambda _: self.descargar_expediente_handler(),
                            ),
                        ],
                        spacing=8,
                        wrap=True,
                        run_spacing=6,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                run_spacing=8,
            ),
        )

        self.pill_shortcut = ft.Container(
            visible=True,
            bgcolor=p["surface_alt"],
            border=ft.border.all(1, p["border"]),
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=7, vertical=2),
            content=ft.Text(
                "Ctrl+F",
                size=11,
                weight=ft.FontWeight.W_600,
                color=p["text_secondary"],
            ),
        )

        self.btn_clear_search = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=p["text_secondary"],
            icon_size=18,
            visible=False,
            tooltip="Limpiar búsqueda",
            on_click=self._limpiar_texto_busqueda,
        )

        self.entrada_busqueda = ft.TextField(
            hint_text="Buscar por nombre de docente o documento...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            suffix=ft.Row(
                [self.pill_shortcut, self.btn_clear_search],
                tight=True,
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            border_radius=12,
            border_color=p["border"],
            focused_border_color=p["primary"],
            bgcolor=p["surface"],
            filled=True,
            color=p["text_primary"],
            cursor_color=p["primary"],
            hint_style=ft.TextStyle(color=p["text_muted"]),
            text_size=14,
            content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
            on_change=self._on_search_change,
            on_submit=lambda _: self.buscar(),
        )

        self.row_chips_filtros = ft.Row(
            visible=False,
            wrap=True,
            spacing=8,
            run_spacing=6,
        )

        self.placeholder_logo = ft.Image(
            src=resource_path("imagenes/logouce3.png"),
            width=210,
            height=210,
            fit=ft.ImageFit.CONTAIN,
        )
        # Panel placeholder inicial
        self.panel_placeholder = ft.Container(
            expand=True,
            visible=True,
            opacity=1.0,
            animate_opacity=anim_smooth(220),
            alignment=ft.alignment.center,
            padding=24,
            content=ft.Column(
                [
                    self.placeholder_logo,
                    ft.Container(height=8),
                    ft.Text(
                        "Usa los filtros y presiona 'Filtrar' para buscar documentos",
                        size=15,
                        weight=ft.FontWeight.W_500,
                        color=p["text_secondary"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Tip: haz doble clic sobre una fila para abrir su PDF directamente",
                        size=12,
                        color=p["text_muted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
        )

        # Panel spinner
        self.lbl_spinner = ft.Text("Cargando documentos...", size=14, color=p["text_secondary"])
        self.panel_spinner = ft.Container(
            visible=False,
            opacity=0.0,
            animate_opacity=anim_smooth(220),
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.ProgressRing(width=42, height=42, stroke_width=4, color=p["primary"]),
                    ft.Container(height=12),
                    self.lbl_spinner,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

        # Cabecera fija de la tabla
        self.chk_todos = ft.Checkbox(
            value=False,
            check_color=p["table_header"],
            active_color=ft.Colors.WHITE,
            border_side=ft.BorderSide(2, ft.Colors.WHITE70),
            tooltip="Seleccionar / deseleccionar todos los de esta página",
            on_change=self._toggle_seleccionar_todos,
        )

        self.col_header_doc = ft.Container(
            expand=4,
            visible=True,
            content=ft.Text(
                "Documento",
                size=13,
                weight=ft.FontWeight.BOLD,
                color=p["table_header_text"],
            ),
        )

        tabla_header = ft.Container(
            bgcolor=p["table_header"],
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            content=ft.Row(
                [
                    ft.Container(width=42, alignment=ft.alignment.center, content=self.chk_todos),
                    ft.Container(
                        expand=3,
                        content=ft.Text(
                            "Estudiante",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=p["table_header_text"],
                        ),
                    ),
                    self.col_header_doc,
                    ft.Container(
                        width=120,
                        alignment=ft.alignment.center,
                        content=ft.Text(
                            "Acciones",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=p["table_header_text"],
                        ),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.lista_resultados = ft.ListView(expand=True, spacing=0, padding=0)
        (
            self.paginador,
            self.lbl_pagina,
            self.btn_prev_pag,
            self.btn_next_pag,
        ) = crear_paginador(self._pagina_anterior, self._pagina_siguiente)

        self.panel_tabla = ft.Container(
            visible=False,
            opacity=0.0,
            animate_opacity=anim_smooth(220),
            expand=True,
            content=ft.Column(
                [
                    tabla_header,
                    self.lista_resultados,
                    self.paginador,
                ],
                spacing=0,
                expand=True,
            ),
        )

        tabla_card = crear_glass_card(
            expand=True,
            border_radius=14,
            padding=0,
            blur_sigma=12,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack(
                [
                    self.panel_placeholder,
                    self.panel_spinner,
                    self.panel_tabla,
                ],
                expand=True,
            ),
        )

        # Barra de estado inferior
        self.lbl_status = ft.Text("Listo", size=12, color=p["text_secondary"], expand=True)
        self.badge_drive, self.icon_drive, self.txt_drive = crear_badge_drive()

        status_bar = crear_glass_card(
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            blur_sigma=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=p["glass_shadow"],
                offset=ft.Offset(0, 2),
            ),
            content=ft.Row(
                [self.lbl_status, self.badge_drive],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.main_content = ft.Container(
            expand=True,
            padding=24,
            content=ft.Column(
                [
                    toolbar,
                    self.entrada_busqueda,
                    self.row_chips_filtros,
                    tabla_card,
                    status_bar,
                ],
                spacing=12,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

        # ------------------------------------------------------------------
        # 2. SIDEBAR DE FILTROS (DERECHA, FIEL AL DISEÑO ORIGINAL)
        # ------------------------------------------------------------------
        def _confirmar_logout(_):
            show_confirm_dialog(
                self.page,
                "Cerrar Sesión",
                "¿Estás seguro de que quieres cerrar sesión?",
                self.on_cerrar_sesion,
                confirm_text="Cerrar sesión",
                confirm_color=p["danger"],
            )

        top_controls: list[ft.Control] = [
            ft.TextButton(
                text="Volver",
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                style=ft.ButtonStyle(color=p["primary"]),
                on_click=lambda _: self.on_volver(),
            ),
        ]
        if self.on_toggle_theme:
            top_controls.append(crear_boton_tema(self.on_toggle_theme, compact=True))
        top_controls.append(
            ft.TextButton(
                text="Cerrar sesión",
                icon=ft.Icons.LOGOUT_ROUNDED,
                style=ft.ButtonStyle(color=p["danger"]),
                on_click=_confirmar_logout,
            )
        )

        sidebar_top = ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, p["divider"])),
            content=ft.Row(
                top_controls,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.combo_universidad = crear_dropdown_filtro(
            "UNIVERSIDAD", ["(Todos)"], on_change=self._on_universidad_change, width=310
        )
        self.combo_programa = crear_dropdown_filtro(
            "PROGRAMA", ["(Todos)"], on_change=self._on_programa_change, width=310
        )
        self.combo_estudiante = crear_dropdown_filtro(
            "ESTUDIANTE", ["(Todos)"], on_change=self._on_estudiante_change, width=310
        )
        self.combo_item_clave = crear_dropdown_filtro(
            "ÍTEM CLAVE", ["(Todos)"], on_change=lambda _: self._actualizar_chips_filtros(), width=310
        )

        self.btn_sincronizar = ft.ElevatedButton(
            text="Sincronizar Documentos",
            icon=ft.Icons.SYNC_ROUNDED,
            bgcolor=p["success"],
            color=ft.Colors.WHITE,
            width=310,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD),
            ),
            on_click=lambda _: self._cargar_documentos(forzar_sincronizacion=True),
        )

        self.lbl_filtros_count = ft.Text("0", size=11, weight=ft.FontWeight.BOLD, color=chip_fg)
        self.badge_filtros_count = ft.Container(
            visible=False,
            bgcolor=p["primary_soft"],
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
            content=self.lbl_filtros_count,
        )

        self.sidebar_logo_col = ft.Column(
            [
                ft.Image(
                    src=resource_path("imagenes/logouce.png"),
                    width=60,
                    height=60,
                    fit=ft.ImageFit.CONTAIN,
                ),
                ft.Container(
                    bgcolor=p["primary_soft"],
                    border_radius=16,
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                    content=ft.Text(
                        "Módulo Doctorados",
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=chip_fg,
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            width=310,
        )

        self.btn_filtrar = ft.ElevatedButton(
            text="Filtrar",
            icon=ft.Icons.SEARCH_ROUNDED,
            bgcolor=p["primary"],
            color=btn_primary_fg,
            width=310,
            height=42,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
            ),
            on_click=lambda _: self.buscar(),
        )

        self.btn_limpiar = ft.OutlinedButton(
            text="Limpiar Filtros",
            icon=ft.Icons.FILTER_ALT_OFF_ROUNDED,
            width=310,
            height=40,
            style=ft.ButtonStyle(
                color=p["text_primary"],
                side=ft.BorderSide(1, p["border"]),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=lambda _: self.limpiar_filtros(),
        )

        sidebar_scroll = ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=12,
                controls=[
                    self.sidebar_logo_col,
                    self.btn_sincronizar,
                    ft.Divider(height=12, color=p["divider"]),
                    ft.Row(
                        [
                            ft.Text(
                                "FILTROS",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=p["text_secondary"],
                            ),
                            self.badge_filtros_count,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.combo_universidad,
                    self.combo_programa,
                    self.combo_estudiante,
                    self.combo_item_clave,
                    ft.Container(height=4),
                    self.btn_filtrar,
                    self.btn_limpiar,
                    ft.Divider(height=16, color=p["divider"]),
                    ft.Container(
                        bgcolor=p["surface_alt"],
                        border=ft.border.all(1, p["border"]),
                        border_radius=10,
                        padding=10,
                        content=ft.Row(
                            [
                                crear_avatar_iniciales(
                                    settings.nombre_usuario_actual or "Usuario",
                                    size=32,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("Sesión activa", size=10, color=p["text_secondary"]),
                                        ft.Text(
                                            settings.nombre_usuario_actual or "Usuario",
                                            size=12,
                                            weight=ft.FontWeight.W_600,
                                            color=p["text_primary"],
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                    ],
                                    spacing=1,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                ],
            ),
        )

        self.sidebar = crear_glass_card(
            width=350,
            border_radius=0,
            padding=0,
            blur_sigma=14,
            is_sidebar=True,
            border=ft.border.only(left=ft.BorderSide(1, p["glass_border"])),
            content=ft.Column([sidebar_top, sidebar_scroll], spacing=0, expand=True),
        )

        return crear_fondo_ambiental(
            ft.Row([self.main_content, self.sidebar], spacing=0, expand=True),
            palette=p,
        )

    def _toggle_sidebar_filtros(self):
        self._sidebar_manual_hidden = not self._sidebar_manual_hidden
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)

    def on_resize(self, width: float, height: float, update_ui: bool = True):
        if not self._activo:
            return
        self._last_vp_width = width
        if width >= 1280:
            sidebar_w, inner_w, pad_main = 350, 310, 24
            self.btn_toggle_filtros.visible = False
            self.sidebar.visible = True
            self._sidebar_manual_hidden = False
        elif width >= 960:
            sidebar_w, inner_w, pad_main = 290, 250, 16
            self.btn_toggle_filtros.visible = False
            self.sidebar.visible = True
            self._sidebar_manual_hidden = False
        else:
            sidebar_w, inner_w, pad_main = 255, 215, 12
            self.btn_toggle_filtros.visible = True
            self.sidebar.visible = not self._sidebar_manual_hidden

        self.sidebar.width = sidebar_w
        self.sidebar_logo_col.width = inner_w
        self.btn_sincronizar.width = inner_w
        self.combo_universidad.width = inner_w
        self.combo_programa.width = inner_w
        self.combo_estudiante.width = inner_w
        self.combo_item_clave.width = inner_w
        self.btn_filtrar.width = inner_w
        self.btn_limpiar.width = inner_w
        self.main_content.padding = pad_main

        logo_sz = 150 if height < 700 else 210
        self.placeholder_logo.width = logo_sz
        self.placeholder_logo.height = logo_sz

        if update_ui:
            self._safe_update()

    def handle_keyboard(self, e: ft.KeyboardEvent):
        """Atajos de teclado: Ctrl+F enfoca buscador, Escape limpia filtros."""
        if not self._activo:
            return
        key = (e.key or "").upper()
        if e.ctrl and key == "F":
            try:
                self.entrada_busqueda.focus()
            except Exception:
                pass
        elif key == "ESCAPE":
            self.limpiar_filtros()

    def on_mount(self, restoring: bool = False):
        """Se ejecuta justo después de montar la vista en la página."""
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)
        if not restoring:
            self._inicializar_filtros(update_ui=True)

            if not settings.ruta_doctorados and not settings.ruta_doctorados2:
                cache = get_cache()
                if not cache.necesita_escaneo():
                    self._cargar_documentos(forzar_sincronizacion=False)
                else:
                    self.lbl_status.value = (
                        "No se encontró ruta de doctorados. Configura o sincroniza desde Ajustes."
                    )
                    self._mostrar_placeholder()
                    self._safe_update()
            else:
                self._cargar_documentos(forzar_sincronizacion=False)

        self._drive_monitor = DriveMonitor(self._on_drive_status)
        self._drive_monitor.start()

    def _on_drive_status(self, conectado: bool):
        if not self._activo:
            return
        actualizar_badge_drive(self.badge_drive, self.icon_drive, self.txt_drive, conectado)

    # ------------------------------------------------------------------
    # FILTROS DEPENDIENTES EN CASCADA Y CHIPS ACTIVOS
    # ------------------------------------------------------------------
    def _inicializar_filtros(self, update_ui: bool = True):
        try:
            universidades = obtener_todas_universidades_combinadas(
                settings.ruta_doctorados, settings.ruta_doctorados2
            )
            if not universidades and settings.documentos_drive:
                universidades = sorted(
                    set(d.get("universidad", "") for d in settings.documentos_drive if d.get("universidad"))
                )
            settings.universidades_lista = universidades
        except Exception as e:
            print(f"[ERROR] obtener universidades: {e}")
            universidades = []

        actualizar_dropdown_opciones(
            self.combo_universidad, ["(Todos)"] + universidades, "(Todos)", update_control=update_ui
        )
        self._actualizar_programas(update_ui=update_ui)
        opciones_items = ["(Todos)"] + sorted(settings.items_clave.keys())
        actualizar_dropdown_opciones(
            self.combo_item_clave, opciones_items, "(Todos)", update_control=update_ui
        )
        self._actualizar_chips_filtros(update_ui=update_ui)

    def _on_universidad_change(self, _=None):
        self._actualizar_programas(update_ui=True)
        self._actualizar_chips_filtros(update_ui=True)

    def _on_programa_change(self, _=None):
        self._actualizar_estudiantes(update_ui=True)
        self._actualizar_chips_filtros(update_ui=True)

    def _on_estudiante_change(self, _=None):
        self._actualizar_items_clave(update_ui=True)
        self._actualizar_chips_filtros(update_ui=True)

    def _actualizar_programas(self, update_ui: bool = True):
        u = normalizar_valor_dropdown(self.combo_universidad.value)
        programas = obtener_programas_filtrados(u)
        actualizar_dropdown_opciones(
            self.combo_programa, ["(Todos)"] + programas, "(Todos)", update_control=update_ui
        )
        self._actualizar_estudiantes(update_ui=update_ui)

    def _actualizar_estudiantes(self, update_ui: bool = True):
        u = normalizar_valor_dropdown(self.combo_universidad.value)
        p_val = normalizar_valor_dropdown(self.combo_programa.value)
        estudiantes = obtener_estudiantes_filtrados(u, p_val)
        actualizar_dropdown_opciones(
            self.combo_estudiante, ["(Todos)"] + estudiantes, "(Todos)", update_control=update_ui
        )
        self._actualizar_items_clave(update_ui=update_ui)

    def _actualizar_items_clave(self, update_ui: bool = True):
        u = normalizar_valor_dropdown(self.combo_universidad.value)
        p_val = normalizar_valor_dropdown(self.combo_programa.value)
        e_val = normalizar_valor_dropdown(self.combo_estudiante.value)
        items = obtener_items_clave_filtrados(u, p_val, e_val)
        actualizar_dropdown_opciones(
            self.combo_item_clave, ["(Todos)"] + items, "(Todos)", update_control=update_ui
        )

    def _quitar_filtro_chip(self, clave: str):
        if clave == "universidad":
            actualizar_dropdown_opciones(
                self.combo_universidad,
                [o.key for o in self.combo_universidad.options] or ["(Todos)"],
                "(Todos)",
            )
            self._actualizar_programas(update_ui=True)
        elif clave == "programa":
            actualizar_dropdown_opciones(
                self.combo_programa,
                [o.key for o in self.combo_programa.options] or ["(Todos)"],
                "(Todos)",
            )
            self._actualizar_estudiantes(update_ui=True)
        elif clave == "estudiante":
            actualizar_dropdown_opciones(
                self.combo_estudiante,
                [o.key for o in self.combo_estudiante.options] or ["(Todos)"],
                "(Todos)",
            )
            self._actualizar_items_clave(update_ui=True)
        elif clave == "item":
            actualizar_dropdown_opciones(
                self.combo_item_clave,
                [o.key for o in self.combo_item_clave.options] or ["(Todos)"],
                "(Todos)",
            )

        self._actualizar_chips_filtros(update_ui=True)
        self._disparar_busqueda_reactiva()

    def _actualizar_chips_filtros(self, update_ui: bool = True):
        u = normalizar_valor_dropdown(self.combo_universidad.value)
        p_val = normalizar_valor_dropdown(self.combo_programa.value)
        e_val = normalizar_valor_dropdown(self.combo_estudiante.value)
        item = normalizar_valor_dropdown(self.combo_item_clave.value)

        activos: list[tuple[str, str, str]] = []
        if u != "(Todos)":
            activos.append(("Universidad", u, "universidad"))
        if p_val != "(Todos)":
            activos.append(("Programa", p_val, "programa"))
        if e_val != "(Todos)":
            activos.append(("Estudiante", e_val, "estudiante"))
        if item != "(Todos)":
            activos.append(("Ítem", item, "item"))

        self.row_chips_filtros.controls.clear()
        for label, val, clave in activos:
            self.row_chips_filtros.controls.append(
                crear_chip_filtro_activo(label, val, lambda c=clave: self._quitar_filtro_chip(c))
            )

        self.row_chips_filtros.visible = bool(activos)
        self.lbl_filtros_count.value = str(len(activos))
        self.badge_filtros_count.visible = bool(activos)

        if update_ui:
            self._safe_update(self.row_chips_filtros)
            self._safe_update(self.badge_filtros_count)

    def limpiar_filtros(self):
        self.entrada_busqueda.value = ""
        self.btn_clear_search.visible = False
        self.pill_shortcut.visible = True
        actualizar_dropdown_opciones(
            self.combo_universidad,
            [o.key for o in self.combo_universidad.options] or ["(Todos)"],
            "(Todos)",
        )
        self._actualizar_programas(update_ui=True)
        self._actualizar_chips_filtros(update_ui=True)
        self._mostrar_placeholder()
        self._safe_update()

    # ------------------------------------------------------------------
    # ESTADOS DE TABLA (Placeholder / Spinner / Resultados)
    # ------------------------------------------------------------------
    def _activar_panel(self, activo: str):
        self.panel_placeholder.visible = activo == "placeholder"
        self.panel_placeholder.opacity = 1.0 if activo == "placeholder" else 0.0

        self.panel_spinner.visible = activo == "spinner"
        self.panel_spinner.opacity = 1.0 if activo == "spinner" else 0.0

        self.panel_tabla.visible = activo == "tabla"
        self.panel_tabla.opacity = 1.0 if activo == "tabla" else 0.0

    def _mostrar_placeholder(self):
        self.resultados_totales = []
        self.selected_paths.clear()
        self.focused_doc = None
        self._actualizar_chip_seleccion()
        self._activar_panel("placeholder")
        self.lbl_status.value = "Usa los filtros y presiona 'Filtrar' para buscar documentos"
        self._safe_update()

    def _mostrar_spinner(self, mensaje: str = "Cargando..."):
        self.lbl_spinner.value = mensaje
        self._activar_panel("spinner")
        self._safe_update()

    def _ocultar_spinner(self):
        self.panel_spinner.visible = False
        self.panel_spinner.opacity = 0.0
        self._safe_update(self.panel_spinner)

    # ------------------------------------------------------------------
    # BÚSQUEDA CON DEBOUNCE Y SEQUENCE LOCK
    # ------------------------------------------------------------------
    def _limpiar_texto_busqueda(self, _=None):
        self.entrada_busqueda.value = ""
        self.btn_clear_search.visible = False
        self.pill_shortcut.visible = True
        self._safe_update(self.entrada_busqueda)
        self._disparar_busqueda_reactiva()

    def _on_search_change(self, e):
        texto = (e.control.value or "").strip()
        self.btn_clear_search.visible = bool(texto)
        self.pill_shortcut.visible = not bool(texto)
        self._safe_update(self.entrada_busqueda)

        if self._search_timer:
            try:
                self._search_timer.cancel()
            except Exception:
                pass
        self._search_timer = threading.Timer(0.3, self._disparar_busqueda_reactiva)
        self._search_timer.daemon = True
        self._search_timer.start()

    def _disparar_busqueda_reactiva(self):
        if not self._activo:
            return
        texto = (self.entrada_busqueda.value or "").strip().lower()
        u = normalizar_valor_dropdown(self.combo_universidad.value)
        p_val = normalizar_valor_dropdown(self.combo_programa.value)
        e_val = normalizar_valor_dropdown(self.combo_estudiante.value)
        item = normalizar_valor_dropdown(self.combo_item_clave.value)

        if not texto and u == "(Todos)" and p_val == "(Todos)" and e_val == "(Todos)" and item == "(Todos)":
            self._mostrar_placeholder()
            return

        self.search_seq += 1
        seq = self.search_seq
        threading.Thread(
            target=self._ejecutar_busqueda_worker,
            args=(u, p_val, e_val, texto, item, seq),
            daemon=True,
        ).start()

    def buscar(self):
        if not self._activo:
            return
        u = normalizar_valor_dropdown(self.combo_universidad.value)
        p_val = normalizar_valor_dropdown(self.combo_programa.value)
        e_val = normalizar_valor_dropdown(self.combo_estudiante.value)
        texto = (self.entrada_busqueda.value or "").strip().lower()
        item = normalizar_valor_dropdown(self.combo_item_clave.value)

        self._actualizar_chips_filtros(update_ui=True)
        self._mostrar_spinner("Filtrando documentos...")
        self.search_seq += 1
        seq = self.search_seq
        threading.Thread(
            target=self._ejecutar_busqueda_worker,
            args=(u, p_val, e_val, texto, item, seq),
            daemon=True,
        ).start()

    def _ejecutar_busqueda_worker(self, u: str, p_val: str, e_val: str, texto: str, item: str, seq: int):
        try:
            encontrados = buscar_documentos(u, p_val, e_val, texto, item)
            if not self._activo or seq != self.search_seq:
                return
            self._poblar_resultados(encontrados, item)
        except Exception as exc:
            print(f"[ERROR] Búsqueda docentes: {exc}")
            if self._activo and seq == self.search_seq:
                self._ocultar_spinner()
                show_snackbar(self.page, f"Error al buscar: {exc}", tipo="error")

    def _poblar_resultados(self, encontrados: list[dict], filtro_item: str):
        self.resultados_totales = encontrados
        self.pagina_actual = 0
        self.selected_paths.clear()
        self.focused_doc = None
        self.mostrar_col_doc = not (filtro_item and filtro_item != "(Todos)")
        self.col_header_doc.visible = self.mostrar_col_doc

        if not encontrados:
            self._activar_panel("placeholder")
            self.lbl_status.value = "Sin resultados para los filtros seleccionados"
            self._actualizar_chip_seleccion()
            self._safe_update()
            return

        self._activar_panel("tabla")
        self._renderizar_pagina()

        total = len(encontrados)
        if total > PAGE_SIZE:
            self.lbl_status.value = f"Mostrando {PAGE_SIZE} por página de {total} documentos encontrados"
        else:
            self.lbl_status.value = f"Mostrando {total} documento(s)"
        self._safe_update()

    def _renderizar_pagina(self):
        p = get_palette()
        total = len(self.resultados_totales)
        total_paginas = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        self.pagina_actual = max(0, min(self.pagina_actual, total_paginas - 1))

        inicio = self.pagina_actual * PAGE_SIZE
        fin = min(inicio + PAGE_SIZE, total)
        slice_docs = self.resultados_totales[inicio:fin]

        self.lista_resultados.controls.clear()
        for idx, doc in enumerate(slice_docs):
            ruta = doc.get("ruta", "")
            bg_base = p["zebra_even"] if idx % 2 == 0 else p["zebra_odd"]
            es_foco = self.focused_doc is not None and self.focused_doc.get("ruta") == ruta
            nombre_doc = limpiar_nombre_documento_docente(doc)
            tipo_doc = obtener_tipo_documento_flet(doc.get("nombre", ""))
            color_punto = COLORES_TIPOS.get(tipo_doc or "", "#94A3B8")
            estudiante = doc.get("estudiante", "").title()
            sub_info = f"{doc.get('universidad', '').title()}  •  {doc.get('programa', '').title()}"

            chk = ft.Checkbox(
                value=ruta in self.selected_paths,
                active_color=p["primary"],
                on_change=lambda e, r=ruta: self._on_row_check(r, bool(e.control.value)),
            )

            fila_container = ft.Container(
                bgcolor=p["row_selected"] if es_foco else bg_base,
                animate=anim_fast(120),
                border=ft.border.only(bottom=ft.BorderSide(1, p["divider"])),
                padding=ft.padding.symmetric(horizontal=14, vertical=7),
                tooltip=f"{sub_info}\nArchivo: {doc.get('nombre', '')}\n(Doble clic para abrir PDF)",
                data=doc,
                content=ft.Row(
                    [
                        ft.Container(width=42, alignment=ft.alignment.center, content=chk),
                        ft.Container(
                            expand=3,
                            content=ft.Column(
                                [
                                    ft.Text(
                                        estudiante,
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=p["text_primary"],
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1,
                                    ),
                                    ft.Text(
                                        sub_info,
                                        size=11,
                                        color=p["text_secondary"],
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1,
                                    ),
                                ],
                                spacing=1,
                                tight=True,
                            ),
                        ),
                        ft.Container(
                            expand=4,
                            visible=self.mostrar_col_doc,
                            content=ft.Row(
                                [
                                    ft.Container(
                                        width=8,
                                        height=8,
                                        border_radius=4,
                                        bgcolor=color_punto,
                                    ),
                                    ft.Text(
                                        nombre_doc,
                                        size=13,
                                        color=p["text_primary"],
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1,
                                        expand=True,
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ),
                        ft.Container(
                            width=120,
                            alignment=ft.alignment.center,
                            content=ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                                        icon_size=18,
                                        icon_color=p["primary"],
                                        tooltip="Abrir PDF",
                                        on_click=lambda _, r=ruta: self._abrir_ruta(r),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.FOLDER_SHARED_OUTLINED,
                                        icon_size=18,
                                        icon_color=p["text_secondary"],
                                        tooltip="Ver todos los documentos del estudiante",
                                        on_click=lambda _, d=doc: self._mostrar_panel_detalles(d),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DOWNLOAD_ROUNDED,
                                        icon_size=18,
                                        icon_color=p["success"],
                                        tooltip="Descargar PDF",
                                        on_click=lambda _, r=ruta: iniciar_descarga_archivos(
                                            self.page, self.file_picker, [r]
                                        ),
                                    ),
                                ],
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

            def _on_click_row(_, d=doc, r=ruta):
                ahora = time.monotonic()
                es_doble = r and r == self._last_click_ruta and (ahora - self._last_click_ts) < 0.4
                self._last_click_ruta = r
                self._last_click_ts = ahora

                self.focused_doc = d
                self._renderizar_pagina()
                self._safe_update(self.panel_tabla)
                if es_doble:
                    self._abrir_ruta(r)

            def _on_hover_row(e, cont=fila_container, base=bg_base, d=doc):
                if self.focused_doc is not None and self.focused_doc.get("ruta") == d.get("ruta"):
                    return
                cont.bgcolor = p["row_hover"] if e.data == "true" else base
                self._safe_update(cont)

            fila_container.on_click = _on_click_row
            fila_container.on_hover = _on_hover_row
            self.lista_resultados.controls.append(fila_container)

        rutas_pagina = {d.get("ruta", "") for d in slice_docs if d.get("ruta")}
        self.chk_todos.value = bool(rutas_pagina) and rutas_pagina.issubset(self.selected_paths)

        self.paginador.visible = total > PAGE_SIZE
        self.lbl_pagina.value = f"Página {self.pagina_actual + 1} de {total_paginas}  ({inicio + 1}–{fin} de {total})"
        self.btn_prev_pag.disabled = self.pagina_actual <= 0
        self.btn_next_pag.disabled = self.pagina_actual >= total_paginas - 1
        self._actualizar_chip_seleccion()

    def _pagina_anterior(self, _):
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self._renderizar_pagina()
            self._safe_update(self.panel_tabla)

    def _pagina_siguiente(self, _):
        total_paginas = max(1, (len(self.resultados_totales) + PAGE_SIZE - 1) // PAGE_SIZE)
        if self.pagina_actual < total_paginas - 1:
            self.pagina_actual += 1
            self._renderizar_pagina()
            self._safe_update(self.panel_tabla)

    def _on_row_check(self, ruta: str, checked: bool):
        if checked:
            self.selected_paths.add(ruta)
        else:
            self.selected_paths.discard(ruta)
        self._actualizar_chip_seleccion()

    def _toggle_seleccionar_todos(self, e):
        inicio = self.pagina_actual * PAGE_SIZE
        fin = min(inicio + PAGE_SIZE, len(self.resultados_totales))
        slice_docs = self.resultados_totales[inicio:fin]
        marcar = bool(e.control.value)
        for d in slice_docs:
            r = d.get("ruta", "")
            if not r:
                continue
            if marcar:
                self.selected_paths.add(r)
            else:
                self.selected_paths.discard(r)
        self._renderizar_pagina()
        self._safe_update(self.panel_tabla)

    def _actualizar_chip_seleccion(self):
        count = len(self.selected_paths)
        self.chip_seleccionados.visible = count > 0
        self.chip_seleccionados.opacity = 1.0 if count > 0 else 0.0
        self.chip_seleccionados.scale = 1.0 if count > 0 else 0.9
        self.lbl_seleccionados.value = f"{count} seleccionado(s)"
        self._safe_update(self.chip_seleccionados)

    # ------------------------------------------------------------------
    # ACCIONES SOBRE DOCUMENTOS Y DETALLES DEL ESTUDIANTE
    # ------------------------------------------------------------------
    def _abrir_ruta(self, ruta: str):
        ok, err = abrir_pdf_flet(ruta)
        if not ok:
            show_snackbar(self.page, err, tipo="error")

    def _rutas_objetivo(self) -> list[str]:
        if self.selected_paths:
            return [d["ruta"] for d in self.resultados_totales if d.get("ruta") in self.selected_paths]
        if self.focused_doc and self.focused_doc.get("ruta"):
            return [self.focused_doc["ruta"]]
        return []

    def abrir_pdf_handler(self):
        rutas = self._rutas_objetivo()
        if not rutas:
            show_snackbar(self.page, "Selecciona un documento para abrir.", tipo="warning")
            return
        for ruta in rutas:
            self._abrir_ruta(ruta)

    def descargar_seleccionados(self):
        rutas = self._rutas_objetivo()
        iniciar_descarga_archivos(
            self.page, self.file_picker, rutas, nombre_zip_base="Documentos_Filtrados"
        )

    def _iniciar_descarga_expediente_doc(self, doc: dict):
        ruta_pdf = doc["ruta"]
        estudiante = doc.get("estudiante", "").title()

        def _on_dir(carpeta: Optional[str]):
            if not carpeta:
                return
            show_snackbar(self.page, f"Comprimiendo expediente de {estudiante}...", tipo="info")

            def _worker():
                ok, res, count = crear_zip_expediente(ruta_pdf, carpeta)
                if ok:
                    show_info_dialog(
                        self.page,
                        "Expediente descargado",
                        f"Expediente guardado exitosamente en:\n{res}\n\nArchivos incluidos: {count}",
                        tipo="success",
                    )
                else:
                    show_info_dialog(self.page, "Error al crear expediente", res, tipo="error")

            threading.Thread(target=_worker, daemon=True).start()

        self.file_picker.get_directory_path(
            _on_dir,
            dialog_title=f"Seleccionar carpeta para guardar expediente de {estudiante}",
        )

    def descargar_expediente_handler(self):
        doc = self.focused_doc
        if not doc and self.selected_paths:
            primera_ruta = next(iter(self.selected_paths))
            doc = next((d for d in self.resultados_totales if d.get("ruta") == primera_ruta), None)

        if not doc or not doc.get("ruta"):
            show_snackbar(
                self.page,
                "Haz clic en un estudiante de la tabla para descargar su expediente completo.",
                tipo="warning",
            )
            return

        self._iniciar_descarga_expediente_doc(doc)

    def _mostrar_panel_detalles(self, doc: dict):
        p = get_palette()
        vp_w, vp_h = get_viewport_size(self.page)
        dlg_w = min(460, max(300, int(vp_w * 0.80)))
        todos_docs = obtener_documentos_estudiante(doc)
        items_btn: list[ft.Control] = []
        vistos = set()

        for d in todos_docs:
            ruta = d.get("ruta", "")
            if not ruta or ruta in vistos:
                continue
            vistos.add(ruta)
            tipo = obtener_tipo_documento_flet(d.get("nombre", "")) or d.get("nombre", "").title()
            color = COLORES_TIPOS.get(tipo, "#475569")
            items_btn.append(
                ft.Row(
                    [
                        ft.ElevatedButton(
                            text=tipo,
                            icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                            bgcolor=color,
                            color=ft.Colors.WHITE,
                            expand=True,
                            height=44,
                            style=ft.ButtonStyle(
                                alignment=ft.alignment.center_left,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                            on_click=lambda _, r=ruta: (self._abrir_ruta(r), self.page.close(dlg)),
                        )
                    ]
                )
            )

        if not items_btn:
            items_btn.append(
                ft.Text("No se encontraron más documentos asociados.", color=p["text_secondary"])
            )

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=p["surface"],
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row(
                [
                    ft.Container(
                        padding=8,
                        border_radius=10,
                        bgcolor=p["primary_soft"],
                        content=ft.Icon(ft.Icons.PERSON_ROUNDED, color=p["primary"], size=24),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                doc.get("estudiante", "").title(),
                                size=17,
                                weight=ft.FontWeight.BOLD,
                                color=p["text_primary"],
                            ),
                            ft.Text(
                                f"{doc.get('universidad', '').title()} — {doc.get('programa', '').title()}",
                                size=12,
                                color=p["text_secondary"],
                            ),
                            ft.Text(
                                f"{len(vistos)} documento(s) disponible(s)",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=p["primary"],
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
            content=ft.Container(
                width=dlg_w,
                height=min(int(vp_h * 0.55), max(120, len(items_btn) * 54)),
                content=ft.Column(items_btn, scroll=ft.ScrollMode.AUTO, spacing=8),
            ),
            actions=[
                ft.ElevatedButton(
                    text="Descargar expediente (.ZIP)",
                    icon=ft.Icons.ARCHIVE_OUTLINED,
                    bgcolor=p["primary"],
                    color="#0B1120" if p["is_dark"] else ft.Colors.WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: (
                        self.page.close(dlg),
                        self._iniciar_descarga_expediente_doc(doc),
                    ),
                ),
                ft.TextButton(
                    text="Cerrar",
                    style=ft.ButtonStyle(color=p["text_secondary"]),
                    on_click=lambda _: self.page.close(dlg),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.page.open(dlg)

    # ------------------------------------------------------------------
    # SINCRONIZACIÓN Y CACHÉ
    # ------------------------------------------------------------------
    def _set_estado_sincronizando(self, sincronizando: bool):
        self.btn_sincronizar.disabled = sincronizando
        self.btn_sincronizar.text = "Sincronizando..." if sincronizando else "Sincronizar Documentos"
        self._safe_update(self.btn_sincronizar)

    def _cargar_documentos(self, forzar_sincronizacion: bool = False):
        if not forzar_sincronizacion and settings.documentos_drive:
            self.lbl_status.value = (
                f"✓ {len(settings.documentos_drive)} documentos cargados (desde memoria)"
            )
            self._ocultar_spinner()
            self._mostrar_placeholder()
            self._inicializar_filtros(update_ui=True)
            return

        cache = get_cache()
        if forzar_sincronizacion:
            if not settings.ruta_doctorados and not settings.ruta_doctorados2:
                r_doc, r_of, r_doc2 = encontrar_rutas_drive()
                settings.ruta_doctorados = settings.ruta_doctorados or r_doc
                settings.ruta_oficios = settings.ruta_oficios or r_of
                settings.ruta_doctorados2 = settings.ruta_doctorados2 or r_doc2

            if not settings.ruta_doctorados and not settings.ruta_doctorados2:
                show_info_dialog(
                    self.page,
                    "Rutas no encontradas",
                    "No se encontraron las rutas de Google Drive para Doctorados.\n"
                    "Verifica que Google Drive esté conectado o configúralas en Ajustes.",
                    tipo="warning",
                )
                return
            cache.invalidate()

        if not cache.necesita_escaneo():
            docs, _ = cache.obtener_documentos()
            settings.documentos_drive = docs or []
            settings.documentos_cargados = True
            self.lbl_status.value = f"✓ {len(settings.documentos_drive)} documentos cargados (desde caché)"
            self._ocultar_spinner()
            self._mostrar_placeholder()
            self._inicializar_filtros(update_ui=True)
            return

        self.lbl_status.value = "Escaneando carpetas de Doctorados..."
        self._set_estado_sincronizando(True)
        self._mostrar_spinner("Sincronizando documentos...")

        def _worker():
            try:
                docs = cache.escanear_con_cache()
                if not self._activo:
                    return
                settings.documentos_drive = docs
                settings.documentos_cargados = True
                self._set_estado_sincronizando(False)
                self._ocultar_spinner()
                self._mostrar_placeholder()
                self._inicializar_filtros(update_ui=True)
                self.lbl_status.value = f"✓ {len(docs)} documentos sincronizados"
                self._safe_update(self.lbl_status)
                if forzar_sincronizacion:
                    show_info_dialog(
                        self.page,
                        "Sincronización completada",
                        f"¡Documentos cargados exitosamente!\n\nTotal: {len(docs)} documentos",
                        tipo="success",
                    )
            except Exception as e:
                if not self._activo:
                    return
                self._set_estado_sincronizando(False)
                self._ocultar_spinner()
                self.lbl_status.value = f"Error al sincronizar: {e}"
                self._safe_update(self.lbl_status)
                show_info_dialog(
                    self.page,
                    "Error de sincronización",
                    f"No se pudieron cargar los documentos:\n{e}",
                    tipo="error",
                )

        threading.Thread(target=_worker, daemon=True).start()
