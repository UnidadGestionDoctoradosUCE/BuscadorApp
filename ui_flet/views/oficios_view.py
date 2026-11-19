"""
Vista del módulo de Oficios en Flet con Glassmorphism, modo Claro/Oscuro dinámico y preservación de estado.
Mantiene fielmente la distribución original: sidebar de filtros a la izquierda y contenido principal a la derecha.
"""
import threading
import time
from typing import Callable, Optional
import flet as ft

import config.settings as settings
from services.file_service import cargar_documentos_oficios
from services.search_service import buscar_oficios, obtener_tipos_oficios_filtrados
from ui_flet.services_bridge import abrir_pdf_flet
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
from utils.file_utils import obtener_estructura_oficios, resource_path
from utils.path_utils import encontrar_rutas_drive

PAGE_SIZE = 100


def _colores_badge_tipo(tipo: str, palette: dict) -> tuple[str, str]:
    t = (tipo or "").lower()
    if "enviad" in t:
        return palette["primary_soft"], palette["primary"] if palette["is_dark"] else palette["primary_dark"]
    if "recibid" in t:
        return palette["success_soft"], palette["success_dark"]
    return palette["surface_alt"], palette["text_primary"]


class OficiosView:
    """Vista moderna del módulo de Oficios con sidebar izquierdo."""

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
        self._search_timer: Optional[threading.Timer] = None
        self._drive_monitor: Optional[DriveMonitor] = None

        self.resultados_totales: list[dict] = []
        self.pagina_actual = 0
        self.selected_paths: set[str] = set()
        self.focused_doc: Optional[dict] = None
        self._last_click_ruta: str = ""
        self._last_click_ts: float = 0.0
        self._sidebar_manual_hidden: bool = False

        # Controles UI
        self.sidebar: ft.Container
        self.sidebar_logo_col: ft.Column
        self.btn_limpiar: ft.OutlinedButton
        self.btn_volver_footer: ft.ElevatedButton
        self.btn_salir_footer: ft.ElevatedButton
        self.main_content: ft.Container
        self.btn_toggle_filtros: ft.OutlinedButton
        self.combo_anio: ft.Dropdown
        self.combo_tipo: ft.Dropdown
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
        self.lista_resultados: ft.ListView

        self.panel_spinner: ft.Container
        self.lbl_spinner: ft.Text
        self.panel_vacio: ft.Container
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
            "anio": normalizar_valor_dropdown(self.combo_anio.value),
            "tipo": normalizar_valor_dropdown(self.combo_tipo.value),
            "resultados": list(self.resultados_totales),
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
        anio = state.get("anio", "(Todos)")
        tipo = state.get("tipo", "(Todos)")

        actualizar_dropdown_opciones(
            self.combo_anio,
            [o.key for o in self.combo_anio.options] or ["(Todos)"],
            anio,
            update_control=False,
        )
        if settings.estructura_oficios:
            tipos = obtener_tipos_oficios_filtrados(anio, settings.estructura_oficios)
        elif settings.documentos_oficios:
            tipos = sorted(
                set(
                    d.get("tipo", "")
                    for d in settings.documentos_oficios
                    if d.get("tipo") and (anio == "(Todos)" or d.get("anio") == anio)
                )
            )
        else:
            tipos = []
        actualizar_dropdown_opciones(
            self.combo_tipo, ["(Todos)"] + tipos, tipo, update_control=False
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
            self._activar_panel("tabla")
            self._renderizar_pagina()
        elif not state.get("resultados"):
            self._activar_panel("vacio")

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
        self.page.title = "Buscador de Oficios"
        btn_primary_fg = "#0B1120" if p["is_dark"] else ft.Colors.WHITE
        chip_fg = p["primary"] if p["is_dark"] else p["primary_dark"]

        def _confirmar_logout(_):
            show_confirm_dialog(
                self.page,
                "Cerrar Sesión",
                "¿Estás seguro de que quieres cerrar sesión?",
                self.on_cerrar_sesion,
                confirm_text="Cerrar sesión",
                confirm_color=p["danger"],
            )

        # ------------------------------------------------------------------
        # 1. SIDEBAR DE FILTROS (IZQUIERDA, FIEL AL DISEÑO ORIGINAL)
        # ------------------------------------------------------------------
        self.combo_anio = crear_dropdown_filtro(
            "AÑO", ["(Todos)"], on_change=self._on_anio_change, width=270
        )
        self.combo_tipo = crear_dropdown_filtro(
            "TIPO", ["(Todos)"], on_change=lambda _: self.buscar(), width=270
        )

        self.btn_sincronizar = ft.ElevatedButton(
            text="Sincronizar Documentos",
            icon=ft.Icons.SYNC_ROUNDED,
            bgcolor=p["success"],
            color=ft.Colors.WHITE,
            width=270,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD),
            ),
            on_click=lambda _: self._cargar_datos(forzar=True),
        )

        self.lbl_filtros_count = ft.Text("0", size=11, weight=ft.FontWeight.BOLD, color=p["danger"])
        self.badge_filtros_count = ft.Container(
            visible=False,
            bgcolor=p["danger_soft"],
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
                    bgcolor=p["danger_soft"],
                    border_radius=16,
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                    content=ft.Text(
                        "Módulo Oficios",
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=p["danger"],
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            width=270,
        )

        self.btn_limpiar = ft.OutlinedButton(
            text="Limpiar Filtros",
            icon=ft.Icons.FILTER_ALT_OFF_ROUNDED,
            width=270,
            height=40,
            style=ft.ButtonStyle(
                color=p["text_primary"],
                side=ft.BorderSide(1, p["border"]),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=lambda _: self.limpiar_filtros(),
        )

        sidebar_cuerpo = ft.Container(
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
                    self.combo_anio,
                    self.combo_tipo,
                    ft.Container(height=4),
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
                                    bgcolor=p["danger"],
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

        self.btn_volver_footer = ft.ElevatedButton(
            text="Volver",
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            bgcolor=p["primary"],
            color=btn_primary_fg,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
            ),
            on_click=lambda _: self.on_volver(),
        )
        self.btn_salir_footer = ft.ElevatedButton(
            text="Salir",
            icon=ft.Icons.LOGOUT_ROUNDED,
            bgcolor=p["danger"],
            color=ft.Colors.WHITE,
            tooltip="Cerrar sesión",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
            ),
            on_click=_confirmar_logout,
        )

        footer_controls: list[ft.Control] = [self.btn_volver_footer]
        if self.on_toggle_theme:
            footer_controls.append(crear_boton_tema(self.on_toggle_theme, compact=True))
        footer_controls.append(self.btn_salir_footer)

        sidebar_footer = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border=ft.border.only(top=ft.BorderSide(1, p["divider"])),
            content=ft.Row(
                footer_controls,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.sidebar = crear_glass_card(
            width=310,
            border_radius=0,
            padding=0,
            blur_sigma=14,
            is_sidebar=True,
            border=ft.border.only(right=ft.BorderSide(1, p["glass_border"])),
            content=ft.Column([sidebar_cuerpo, sidebar_footer], spacing=0, expand=True),
        )

        # ------------------------------------------------------------------
        # 2. CONTENIDO PRINCIPAL (DERECHA)
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
                                        "BUSCADOR DE OFICIOS",
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
                                "Documentación oficial y correspondencia",
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
                                on_click=lambda _: self.descargar_pdf_handler(),
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
            hint_text="Buscar por nombre o número...",
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

        # Spinner
        self.lbl_spinner = ft.Text("Cargando oficios...", size=14, color=p["text_secondary"])
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

        # Estado vacío
        self.panel_vacio = ft.Container(
            visible=False,
            opacity=0.0,
            animate_opacity=anim_smooth(220),
            expand=True,
            alignment=ft.alignment.center,
            padding=24,
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.FIND_IN_PAGE_OUTLINED, size=64, color=p["text_muted"]),
                    ft.Container(height=8),
                    ft.Text(
                        "No se encontraron oficios con los filtros actuales",
                        size=15,
                        color=p["text_secondary"],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

        # Cabecera fija de tabla
        self.chk_todos = ft.Checkbox(
            value=False,
            check_color=p["table_header"],
            active_color=ft.Colors.WHITE,
            border_side=ft.BorderSide(2, ft.Colors.WHITE70),
            tooltip="Seleccionar / deseleccionar todos los de esta página",
            on_change=self._toggle_seleccionar_todos,
        )

        tabla_header = ft.Container(
            bgcolor=p["table_header"],
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            content=ft.Row(
                [
                    ft.Container(width=42, alignment=ft.alignment.center, content=self.chk_todos),
                    ft.Container(
                        width=80,
                        alignment=ft.alignment.center,
                        content=ft.Text("Año", size=13, weight=ft.FontWeight.BOLD, color=p["table_header_text"]),
                    ),
                    ft.Container(
                        expand=2,
                        content=ft.Text("Tipo", size=13, weight=ft.FontWeight.BOLD, color=p["table_header_text"]),
                    ),
                    ft.Container(
                        expand=5,
                        content=ft.Text(
                            "Nombre del Oficio",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=p["table_header_text"],
                        ),
                    ),
                    ft.Container(
                        width=86,
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
            visible=True,
            opacity=1.0,
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
                    self.panel_vacio,
                    self.panel_spinner,
                    self.panel_tabla,
                ],
                expand=True,
            ),
        )

        # Barra de estado
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

        return crear_fondo_ambiental(
            ft.Row([self.sidebar, self.main_content], spacing=0, expand=True),
            palette=p,
        )

    def _toggle_sidebar_filtros(self):
        self._sidebar_manual_hidden = not self._sidebar_manual_hidden
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)

    def on_resize(self, width: float, height: float, update_ui: bool = True):
        if not self._activo:
            return
        if width >= 1280:
            sidebar_w, inner_w, pad_main = 310, 270, 24
            self.btn_toggle_filtros.visible = False
            self.sidebar.visible = True
            self._sidebar_manual_hidden = False
        elif width >= 960:
            sidebar_w, inner_w, pad_main = 275, 235, 16
            self.btn_toggle_filtros.visible = False
            self.sidebar.visible = True
            self._sidebar_manual_hidden = False
        else:
            sidebar_w, inner_w, pad_main = 250, 210, 12
            self.btn_toggle_filtros.visible = True
            self.sidebar.visible = not self._sidebar_manual_hidden

        self.sidebar.width = sidebar_w
        self.sidebar_logo_col.width = inner_w
        self.btn_sincronizar.width = inner_w
        self.combo_anio.width = inner_w
        self.combo_tipo.width = inner_w
        self.btn_limpiar.width = inner_w
        self.main_content.padding = pad_main
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
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)
        if not restoring:
            self._inicializar_filtros(update_ui=True)
            if not settings.ruta_oficios:
                self.lbl_status.value = "No se encontró la ruta de oficios. Configúrala en Ajustes."
                self._activar_panel("vacio")
                self._safe_update()
            else:
                self._cargar_datos(forzar=False)

        self._drive_monitor = DriveMonitor(self._on_drive_status)
        self._drive_monitor.start()

    def _on_drive_status(self, conectado: bool):
        if not self._activo:
            return
        actualizar_badge_drive(self.badge_drive, self.icon_drive, self.txt_drive, conectado)

    def _activar_panel(self, activo: str):
        self.panel_vacio.visible = activo == "vacio"
        self.panel_vacio.opacity = 1.0 if activo == "vacio" else 0.0

        self.panel_spinner.visible = activo == "spinner"
        self.panel_spinner.opacity = 1.0 if activo == "spinner" else 0.0

        self.panel_tabla.visible = activo == "tabla"
        self.panel_tabla.opacity = 1.0 if activo == "tabla" else 0.0

    # ------------------------------------------------------------------
    # FILTROS Y CHIPS ACTIVOS
    # ------------------------------------------------------------------
    def _inicializar_filtros(self, update_ui: bool = True):
        if settings.estructura_oficios:
            anios = sorted(settings.estructura_oficios.keys())
            tipos = obtener_tipos_oficios_filtrados("(Todos)", settings.estructura_oficios)
        elif settings.documentos_oficios:
            anios = sorted(
                set(d.get("anio", "") for d in settings.documentos_oficios if d.get("anio"))
            )
            tipos = sorted(
                set(d.get("tipo", "") for d in settings.documentos_oficios if d.get("tipo"))
            )
        else:
            anios = []
            tipos = []

        actualizar_dropdown_opciones(
            self.combo_anio, ["(Todos)"] + anios, "(Todos)", update_control=update_ui
        )
        actualizar_dropdown_opciones(
            self.combo_tipo, ["(Todos)"] + tipos, "(Todos)", update_control=update_ui
        )
        self._actualizar_chips_filtros(update_ui=update_ui)

    def _on_anio_change(self, _=None):
        anio = normalizar_valor_dropdown(self.combo_anio.value)
        if settings.estructura_oficios:
            tipos = obtener_tipos_oficios_filtrados(anio, settings.estructura_oficios)
        elif settings.documentos_oficios:
            tipos = sorted(
                set(
                    d.get("tipo", "")
                    for d in settings.documentos_oficios
                    if d.get("tipo") and (anio == "(Todos)" or d.get("anio") == anio)
                )
            )
        else:
            tipos = []
        actualizar_dropdown_opciones(
            self.combo_tipo, ["(Todos)"] + tipos, "(Todos)", update_control=True
        )
        self.buscar()

    def _quitar_filtro_chip(self, clave: str):
        if clave == "anio":
            actualizar_dropdown_opciones(
                self.combo_anio,
                [o.key for o in self.combo_anio.options] or ["(Todos)"],
                "(Todos)",
            )
            self._on_anio_change()
            return
        if clave == "tipo":
            actualizar_dropdown_opciones(
                self.combo_tipo,
                [o.key for o in self.combo_tipo.options] or ["(Todos)"],
                "(Todos)",
            )
            self.buscar()

    def _actualizar_chips_filtros(self, update_ui: bool = True):
        anio = normalizar_valor_dropdown(self.combo_anio.value)
        tipo = normalizar_valor_dropdown(self.combo_tipo.value)

        activos: list[tuple[str, str, str]] = []
        if anio != "(Todos)":
            activos.append(("Año", anio, "anio"))
        if tipo != "(Todos)":
            activos.append(("Tipo", tipo, "tipo"))

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
        self._inicializar_filtros(update_ui=True)
        self.buscar()

    # ------------------------------------------------------------------
    # BÚSQUEDA Y RESULTADOS
    # ------------------------------------------------------------------
    def _limpiar_texto_busqueda(self, _=None):
        self.entrada_busqueda.value = ""
        self.btn_clear_search.visible = False
        self.pill_shortcut.visible = True
        self._safe_update(self.entrada_busqueda)
        self.buscar()

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
        self._search_timer = threading.Timer(0.3, self.buscar)
        self._search_timer.daemon = True
        self._search_timer.start()

    def buscar(self):
        if not self._activo:
            return
        anio = normalizar_valor_dropdown(self.combo_anio.value)
        tipo = normalizar_valor_dropdown(self.combo_tipo.value)
        texto = (self.entrada_busqueda.value or "").strip().lower()

        self._actualizar_chips_filtros(update_ui=True)
        encontrados = buscar_oficios(anio, tipo, texto)
        self._poblar_resultados(encontrados)

    def _poblar_resultados(self, encontrados: list[dict]):
        self.resultados_totales = encontrados
        self.pagina_actual = 0
        self.selected_paths.clear()
        self.focused_doc = None

        if not encontrados:
            self._activar_panel("vacio")
            self.lbl_status.value = "Sin resultados"
            self._actualizar_chip_seleccion()
            self._safe_update()
            return

        self._activar_panel("tabla")
        self._renderizar_pagina()

        total = len(encontrados)
        if total > PAGE_SIZE:
            self.lbl_status.value = f"Mostrando {PAGE_SIZE} por página de {total} oficio(s)"
        else:
            self.lbl_status.value = f"Mostrando {total} resultado(s)"
        self._safe_update()

    def _renderizar_pagina(self):
        p = get_palette()
        chip_fg = p["primary"] if p["is_dark"] else p["primary_dark"]
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
            nombre_completo = doc.get("nombre", "")
            anio_str = str(doc.get("anio", ""))
            tipo_str = str(doc.get("tipo", ""))
            tipo_bg, tipo_fg = _colores_badge_tipo(tipo_str, p)

            chk = ft.Checkbox(
                value=ruta in self.selected_paths,
                active_color=p["primary"],
                on_change=lambda e, r=ruta: self._on_row_check(r, bool(e.control.value)),
            )

            fila_container = ft.Container(
                bgcolor=p["row_selected"] if es_foco else bg_base,
                animate=anim_fast(120),
                border=ft.border.only(bottom=ft.BorderSide(1, p["divider"])),
                padding=ft.padding.symmetric(horizontal=14, vertical=6),
                tooltip=f"{anio_str} • {tipo_str}\n{nombre_completo}\n(Doble clic para abrir PDF)",
                content=ft.Row(
                    [
                        ft.Container(width=42, alignment=ft.alignment.center, content=chk),
                        ft.Container(
                            width=80,
                            alignment=ft.alignment.center,
                            content=ft.Container(
                                bgcolor=p["primary_soft"],
                                border_radius=12,
                                padding=ft.padding.symmetric(horizontal=10, vertical=3),
                                content=ft.Text(
                                    anio_str or "-",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=chip_fg,
                                ),
                            ),
                        ),
                        ft.Container(
                            expand=2,
                            alignment=ft.alignment.center_left,
                            content=ft.Container(
                                bgcolor=tipo_bg,
                                border_radius=12,
                                padding=ft.padding.symmetric(horizontal=10, vertical=3),
                                content=ft.Text(
                                    tipo_str or "-",
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=tipo_fg,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    max_lines=1,
                                ),
                            ),
                        ),
                        ft.Container(
                            expand=5,
                            content=ft.Text(
                                nombre_completo,
                                size=13,
                                weight=ft.FontWeight.W_500,
                                color=p["text_primary"],
                                overflow=ft.TextOverflow.ELLIPSIS,
                                max_lines=1,
                            ),
                        ),
                        ft.Container(
                            width=86,
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
                                        icon=ft.Icons.DOWNLOAD_ROUNDED,
                                        icon_size=18,
                                        icon_color=p["success"],
                                        tooltip="Descargar PDF",
                                        on_click=lambda _, r=ruta: iniciar_descarga_archivos(
                                            self.page,
                                            self.file_picker,
                                            [r],
                                            nombre_zip_base="Oficios_Seleccionados",
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
    # ACCIONES Y CARGA
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
            show_snackbar(self.page, "Selecciona un oficio para abrir.", tipo="warning")
            return
        for ruta in rutas:
            self._abrir_ruta(ruta)

    def descargar_pdf_handler(self):
        rutas = self._rutas_objetivo()
        iniciar_descarga_archivos(
            self.page, self.file_picker, rutas, nombre_zip_base="Oficios_Filtrados"
        )

    def _set_estado_sincronizando(self, sincronizando: bool):
        self.btn_sincronizar.disabled = sincronizando
        self.btn_sincronizar.text = "Sincronizando..." if sincronizando else "Sincronizar Documentos"
        self._safe_update(self.btn_sincronizar)

    def _cargar_datos(self, forzar: bool = False):
        if forzar or not settings.ruta_oficios:
            if not settings.ruta_oficios:
                _, r_of, _ = encontrar_rutas_drive()
                if r_of:
                    settings.ruta_oficios = r_of

        if not settings.ruta_oficios:
            show_info_dialog(
                self.page,
                "Ruta de Oficios no encontrada",
                "No se pudo detectar la carpeta de Oficios en Google Drive.\n"
                "Verifica la conexión o configúrala en Ajustes.",
                tipo="warning",
            )
            return

        if not forzar and settings.oficios_cargados:
            total = len(settings.documentos_oficios)
            self._inicializar_filtros(update_ui=True)
            self.buscar()
            self.lbl_status.value = f"✓ {total} documentos cargados (en caché)"
            self._safe_update(self.lbl_status)
            return

        self.lbl_spinner.value = "Escaneando carpeta de oficios..."
        self.lbl_status.value = "Escaneando oficios..."
        self._set_estado_sincronizando(True)
        self._activar_panel("spinner")
        self._safe_update()

        def _worker():
            try:
                settings.estructura_oficios = obtener_estructura_oficios(settings.ruta_oficios)
                settings.documentos_oficios = cargar_documentos_oficios(settings.ruta_oficios, None)
                settings.oficios_cargados = True
                if not self._activo:
                    return
                total = len(settings.documentos_oficios)
                self._set_estado_sincronizando(False)
                self._inicializar_filtros(update_ui=True)
                self.buscar()
                self.lbl_status.value = f"✓ {total} oficios cargados"
                self._safe_update(self.lbl_status)
                if forzar:
                    show_info_dialog(
                        self.page,
                        "Sincronización completada",
                        f"¡Oficios cargados exitosamente!\n\nTotal: {total} documentos",
                        tipo="success",
                    )
            except Exception as e:
                if not self._activo:
                    return
                self._set_estado_sincronizando(False)
                self._activar_panel("vacio")
                self.lbl_status.value = f"Error: {e}"
                self._safe_update()
                show_info_dialog(
                    self.page,
                    "Error al cargar oficios",
                    f"No se pudieron escanear los oficios:\n{e}",
                    tipo="error",
                )

        threading.Thread(target=_worker, daemon=True).start()
