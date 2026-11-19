"""
Vista de Acerca de en Flet responsive con Glassmorphism, modo Claro/Oscuro dinámico y filete oro académico.
"""
import platform
import threading
from typing import Callable, Optional
import flet as ft

from ui_flet.theme import (
    anim_smooth,
    crear_avatar_iniciales,
    crear_boton_tema,
    crear_fondo_ambiental,
    crear_glass_card,
    get_palette,
    get_viewport_size,
    programar_timer,
)
from utils.file_utils import resource_path


class AcercaDeView:
    """Vista informativa responsive de la aplicación."""

    def __init__(
        self,
        page: ft.Page,
        on_volver: Callable[[], None],
        on_toggle_theme: Optional[Callable[[], None]] = None,
    ):
        self.page = page
        self.on_volver = on_volver
        self.on_toggle_theme = on_toggle_theme
        self._activo = True
        self._timers: list[threading.Timer] = []

        self.sidebar: ft.Container
        self.btn_volver: ft.ElevatedButton
        self.col_tecnica: ft.Column
        self.col_equipo: ft.Column
        self.info_rows_holder: ft.Container
        self.contenido_container: ft.Container
        self.card_info: ft.Container
        self._modo_apilado: Optional[bool] = None

    def dispose(self):
        self._activo = False
        for t in self._timers:
            try:
                t.cancel()
            except Exception:
                pass
        self._timers.clear()

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

    def _info_row(self, icono: str, label: str, valor: str) -> ft.Row:
        p = get_palette()
        return ft.Row(
            [
                ft.Container(
                    width=38,
                    height=38,
                    border_radius=10,
                    bgcolor=p["primary_soft"],
                    alignment=ft.alignment.center,
                    content=ft.Icon(icono, size=18, color=p["primary"]),
                ),
                ft.Column(
                    [
                        ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=p["text_secondary"]),
                        ft.Text(valor, size=14, weight=ft.FontWeight.W_600, color=p["text_primary"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def build(self) -> ft.Control:
        p = get_palette()
        self.page.title = "Acerca de - Buscador de Documentos"

        self.btn_volver = ft.ElevatedButton(
            text="Volver",
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            bgcolor=p["primary"],
            color="#0B1120" if p["is_dark"] else ft.Colors.WHITE,
            width=212,
            height=42,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=lambda _: self.on_volver(),
        )

        sidebar_controls: list[ft.Control] = [
            ft.Container(
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=12),
                content=ft.Image(
                    src=resource_path("imagenes/logouce.png"),
                    width=84,
                    height=84,
                    fit=ft.ImageFit.CONTAIN,
                ),
            ),
            ft.Text(
                "Buscador de\nDocumentos",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=p["text_primary"],
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Divider(height=24, color=p["divider"]),
            self.btn_volver,
        ]
        if self.on_toggle_theme:
            sidebar_controls.append(crear_boton_tema(self.on_toggle_theme, compact=False))

        self.sidebar = crear_glass_card(
            width=260,
            border_radius=0,
            padding=24,
            blur_sigma=14,
            is_sidebar=True,
            border=ft.border.only(right=ft.BorderSide(1, p["glass_border"])),
            content=ft.Column(
                sidebar_controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
        )

        self.col_tecnica = ft.Column(
            [
                ft.Text("Detalles Técnicos", size=16, weight=ft.FontWeight.BOLD, color=p["text_primary"]),
                ft.Container(height=8),
                self._info_row(ft.Icons.NEW_RELEASES_OUTLINED, "Versión", "2.0.0"),
                ft.Divider(height=16, color=p["divider"]),
                self._info_row(
                    ft.Icons.CODE_ROUNDED,
                    "Lenguaje de Programación",
                    f"Python {platform.python_version()}",
                ),
                ft.Divider(height=16, color=p["divider"]),
                self._info_row(
                    ft.Icons.DESKTOP_WINDOWS_ROUNDED,
                    "Interfaz Gráfica",
                    "Flet (Flutter Desktop + Glassmorphism)",
                ),
            ],
            expand=True,
            spacing=6,
        )

        desarrolladores = [
            ("Bryan Loya", "#0F3D75"),
            ("Wulfer Quiguango", "#0284C7"),
            ("Marielena Gonzalez", "#059669"),
            ("Mariel Milan", "#6366F1"),
        ]

        dev_cards = [
            ft.Container(
                bgcolor=p["surface_alt"],
                border=ft.border.all(1, p["border"]),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                content=ft.Row(
                    [
                        crear_avatar_iniciales(dev, size=32, bgcolor=color),
                        ft.Text(
                            dev,
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=p["text_primary"],
                        ),
                    ],
                    spacing=10,
                ),
            )
            for dev, color in desarrolladores
        ]

        self.col_equipo = ft.Column(
            [
                ft.Text("Equipo y Universidad", size=16, weight=ft.FontWeight.BOLD, color=p["text_primary"]),
                ft.Container(height=8),
                self._info_row(
                    ft.Icons.ACCOUNT_BALANCE_ROUNDED,
                    "Universidad",
                    "Universidad Central del Ecuador",
                ),
                ft.Divider(height=16, color=p["divider"]),
                self._info_row(
                    ft.Icons.SCHOOL_ROUNDED,
                    "Carrera",
                    "Ingeniería en Ciencias de la Computación",
                ),
                ft.Divider(height=16, color=p["divider"]),
                ft.Text("Desarrolladores", size=12, weight=ft.FontWeight.W_600, color=p["text_secondary"]),
                ft.Column(dev_cards, spacing=8),
            ],
            expand=True,
            spacing=6,
        )

        self.info_rows_holder = ft.Container(
            padding=32,
            content=ft.Row(
                [
                    self.col_tecnica,
                    ft.VerticalDivider(width=32, color=p["divider"]),
                    self.col_equipo,
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=16,
            ),
        )

        self.card_info = crear_glass_card(
            border_radius=20,
            padding=0,
            blur_sigma=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            opacity=0.0,
            offset=ft.Offset(0, 0.03),
            animate_opacity=anim_smooth(300),
            animate_offset=anim_smooth(300),
            content=ft.Column(
                [
                    ft.Container(height=4, bgcolor=p["gold"]),
                    self.info_rows_holder,
                ],
                spacing=0,
                tight=True,
            ),
        )

        self.contenido_container = ft.Container(
            expand=True,
            padding=40,
            content=ft.Column(
                [
                    ft.Text(
                        "Acerca de la Aplicación",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=p["text_primary"],
                    ),
                    ft.Text(
                        "Sistema de búsqueda y gestión de expedientes de doctorados y oficios.",
                        size=14,
                        color=p["text_secondary"],
                    ),
                    ft.Container(height=12),
                    self.card_info,
                    ft.Container(height=16),
                    ft.Text(
                        "© Universidad Central del Ecuador - Todos los derechos reservados",
                        size=12,
                        color=p["text_secondary"],
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=6,
                expand=True,
            ),
        )

        return crear_fondo_ambiental(
            ft.Row([self.sidebar, self.contenido_container], spacing=0, expand=True),
            palette=p,
        )

    def on_resize(self, width: float, height: float, update_ui: bool = True):
        if not self._activo:
            return
        p = get_palette()
        apilado = width < 920

        if width < 960:
            self.sidebar.width = 210
            self.btn_volver.width = 162
            self.contenido_container.padding = 20
        else:
            self.sidebar.width = 260
            self.btn_volver.width = 212
            self.contenido_container.padding = 40

        if apilado != self._modo_apilado:
            self._modo_apilado = apilado
            if apilado:
                self.col_tecnica.expand = False
                self.col_equipo.expand = False
                self.info_rows_holder.padding = 20
                self.info_rows_holder.content = ft.Column(
                    [
                        self.col_tecnica,
                        ft.Divider(height=20, color=p["divider"]),
                        self.col_equipo,
                    ],
                    spacing=8,
                )
            else:
                self.col_tecnica.expand = True
                self.col_equipo.expand = True
                self.info_rows_holder.padding = 32
                self.info_rows_holder.content = ft.Row(
                    [
                        self.col_tecnica,
                        ft.VerticalDivider(width=32, color=p["divider"]),
                        self.col_equipo,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=16,
                )

        if update_ui:
            self._safe_update()

    def on_mount(self, restoring: bool = False):
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)
        self._timers.append(programar_timer(0.04, self._animar_entrada))

    def _animar_entrada(self):
        if not self._activo:
            return
        self.card_info.opacity = 1.0
        self.card_info.offset = ft.Offset(0, 0)
        self._safe_update(self.card_info)
