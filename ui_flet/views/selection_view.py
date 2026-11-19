"""
Vista ejecutiva y responsive de selección de módulos (Docentes / Oficios) en Flet.
Incluye Glassmorphism real, KPIs institucionales en vivo, modo Claro/Oscuro y animaciones hover.
"""
from datetime import datetime
import threading
from typing import Callable, Optional
import flet as ft

import config.settings as settings
from services.cache_service import get_cache
from ui_flet.components.config_dialog import abrir_config_dialog
from ui_flet.theme import (
    DriveMonitor,
    FilePickerHelper,
    actualizar_badge_drive,
    anim_smooth,
    crear_avatar_iniciales,
    crear_badge_drive,
    crear_boton_tema,
    crear_fondo_ambiental,
    crear_glass_card,
    get_palette,
    get_viewport_size,
    programar_timer,
    show_confirm_dialog,
)
from utils.file_utils import resource_path


def _saludo_segun_hora() -> str:
    hora = datetime.now().hour
    if 5 <= hora < 12:
        return "Buenos días"
    if 12 <= hora < 19:
        return "Buenas tardes"
    return "Buenas noches"


def _calcular_kpis_cache() -> dict[str, int]:
    """Obtiene métricas ejecutivas desde memoria o caché rápido sin bloquear el hilo UI."""
    docs = settings.documentos_drive
    if not docs:
        try:
            cache = get_cache()
            if not cache.necesita_escaneo():
                docs_cache, _ = cache.obtener_documentos()
                if docs_cache:
                    docs = docs_cache
                    settings.documentos_drive = docs
                    settings.documentos_cargados = True
        except Exception:
            docs = []

    if not docs:
        return {"docs": 0, "universidades": 0, "programas": 0, "estudiantes": 0}

    univs = {d.get("universidad_norm") or d.get("universidad") for d in docs if d.get("universidad")}
    progs = {d.get("programa_norm") or d.get("programa") for d in docs if d.get("programa")}
    ests = {d.get("estudiante_norm") or d.get("estudiante") for d in docs if d.get("estudiante")}
    return {
        "docs": len(docs),
        "universidades": len(univs),
        "programas": len(progs),
        "estudiantes": len(ests),
    }


class SelectionView:
    """Pantalla principal ejecutiva de selección de módulos."""

    def __init__(
        self,
        page: ft.Page,
        file_picker: FilePickerHelper,
        nombre_usuario: str,
        on_docentes: Callable[[], None],
        on_oficios: Callable[[], None],
        on_acerca_de: Callable[[], None],
        on_cerrar_sesion: Callable[[], None],
        on_toggle_theme: Optional[Callable[[], None]] = None,
        on_set_theme: Optional[Callable[[str], None]] = None,
    ):
        self.page = page
        self.file_picker = file_picker
        self.nombre_usuario = nombre_usuario
        self.on_docentes = on_docentes
        self.on_oficios = on_oficios
        self.on_acerca_de = on_acerca_de
        self.on_cerrar_sesion = on_cerrar_sesion
        self.on_toggle_theme = on_toggle_theme
        self.on_set_theme = on_set_theme

        self._activo = True
        self._timers: list[threading.Timer] = []
        self._drive_monitor: Optional[DriveMonitor] = None

        self.top_bar: ft.Container
        self.lbl_subtitulo_app: ft.Text
        self.lbl_nombre_usuario: ft.Text
        self.lbl_saludo: ft.Text
        self.badge_drive: ft.Container
        self.icon_drive: ft.Icon
        self.txt_drive: ft.Text
        self.kpi_cards: list[ft.Container] = []
        self.kpi_strip: ft.Container
        self.card_docentes: ft.Container
        self.card_oficios: ft.Container

    def dispose(self):
        self._activo = False
        for t in self._timers:
            try:
                t.cancel()
            except Exception:
                pass
        self._timers.clear()
        if self._drive_monitor:
            self._drive_monitor.stop()
            self._drive_monitor = None

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

    def _crear_kpi_card(self, titulo: str, valor: int, icono: str, color_icono: str) -> ft.Container:
        p = get_palette()
        return crear_glass_card(
            width=185,
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            blur_sigma=12,
            content=ft.Row(
                [
                    ft.Container(
                        width=36,
                        height=36,
                        border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.14, color_icono),
                        alignment=ft.alignment.center,
                        content=ft.Icon(icono, size=19, color=color_icono),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                f"{valor:,}",
                                size=17,
                                weight=ft.FontWeight.BOLD,
                                color=p["text_primary"],
                            ),
                            ft.Text(
                                titulo,
                                size=11,
                                color=p["text_secondary"],
                                max_lines=1,
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
        )

    def _crear_tarjeta_modulo(
        self,
        titulo: str,
        descripcion: str,
        icono: str,
        color_acento: str,
        color_fondo_icono: str,
        on_click: Callable[[], None],
    ) -> ft.Container:
        p = get_palette()
        btn_text_color = "#0B1120" if (p["is_dark"] and color_acento == p["primary"]) else ft.Colors.WHITE

        card = crear_glass_card(
            width=350,
            border_radius=20,
            padding=0,
            blur_sigma=16,
            border=ft.border.all(1.5, p["glass_border"]),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            opacity=0.0,
            scale=1.0,
            offset=ft.Offset(0, 0.04),
            animate=anim_smooth(200),
            animate_opacity=anim_smooth(320),
            animate_scale=anim_smooth(200),
            animate_offset=anim_smooth(260),
            on_click=lambda _: on_click(),
            content=ft.Column(
                [
                    ft.Container(height=5, bgcolor=color_acento),
                    ft.Container(
                        padding=28,
                        content=ft.Column(
                            [
                                ft.Container(
                                    width=82,
                                    height=82,
                                    border_radius=41,
                                    bgcolor=color_fondo_icono,
                                    border=ft.border.all(1, ft.Colors.with_opacity(0.22, color_acento)),
                                    alignment=ft.alignment.center,
                                    content=ft.Icon(icono, size=40, color=color_acento),
                                ),
                                ft.Container(height=10),
                                ft.Text(
                                    titulo,
                                    size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=p["text_primary"],
                                ),
                                ft.Text(
                                    descripcion,
                                    size=13,
                                    color=p["text_secondary"],
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(height=14),
                                ft.ElevatedButton(
                                    text="ACCEDER",
                                    icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                    bgcolor=color_acento,
                                    color=btn_text_color,
                                    width=220,
                                    height=44,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                                    ),
                                    on_click=lambda _: on_click(),
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                    ),
                ],
                spacing=0,
                tight=True,
            ),
        )

        def _on_hover(e: ft.HoverEvent):
            if not self._activo:
                return
            is_hover = e.data == "true"
            card.border = ft.border.all(
                2 if is_hover else 1.5,
                color_acento if is_hover else p["glass_border"],
            )
            card.scale = 1.025 if is_hover else 1.0
            card.offset = ft.Offset(0, -0.015) if is_hover else ft.Offset(0, 0)
            card.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=30 if is_hover else 24,
                color=ft.Colors.with_opacity(0.22 if is_hover else 0.10, color_acento)
                if is_hover
                else p["glass_shadow"],
                offset=ft.Offset(0, 12 if is_hover else 8),
            )
            self._safe_update(card)

        card.on_hover = _on_hover
        return card

    def build(self) -> ft.Control:
        p = get_palette()
        self.page.title = "BuscadorApp — Seleccione una opción"

        def _confirmar_logout(_):
            show_confirm_dialog(
                self.page,
                "Cerrar Sesión",
                "¿Estás seguro de que quieres cerrar sesión?",
                self.on_cerrar_sesion,
                confirm_text="Cerrar sesión",
                confirm_color=p["danger"],
            )

        self.badge_drive, self.icon_drive, self.txt_drive = crear_badge_drive()
        self.lbl_subtitulo_app = ft.Text(
            "Universidad Central del Ecuador",
            size=11,
            color=p["text_secondary"],
        )
        self.lbl_nombre_usuario = ft.Text(
            self.nombre_usuario,
            size=13,
            weight=ft.FontWeight.W_600,
            color=p["text_primary"],
        )

        acciones_header: list[ft.Control] = [self.badge_drive]
        if self.on_toggle_theme:
            acciones_header.append(crear_boton_tema(self.on_toggle_theme, compact=True))
        acciones_header.extend(
            [
                crear_avatar_iniciales(self.nombre_usuario, size=34),
                self.lbl_nombre_usuario,
                ft.OutlinedButton(
                    text="Ajustes",
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    style=ft.ButtonStyle(
                        color=p["text_primary"],
                        side=ft.BorderSide(1, p["border"]),
                        shape=ft.RoundedRectangleBorder(radius=10),
                        bgcolor=p["surface_alt"],
                    ),
                    on_click=lambda _: abrir_config_dialog(
                        self.page,
                        self.file_picker,
                        on_theme_change=self.on_set_theme,
                    ),
                ),
                ft.OutlinedButton(
                    text="Cerrar sesión",
                    icon=ft.Icons.LOGOUT_ROUNDED,
                    style=ft.ButtonStyle(
                        color=p["danger"],
                        side=ft.BorderSide(1, ft.Colors.with_opacity(0.35, p["danger"])),
                        shape=ft.RoundedRectangleBorder(radius=10),
                        bgcolor=p["surface_alt"],
                    ),
                    on_click=_confirmar_logout,
                ),
            ]
        )

        self.top_bar = crear_glass_card(
            height=68,
            border_radius=0,
            blur_sigma=14,
            is_sidebar=True,
            padding=ft.padding.symmetric(horizontal=28),
            border=ft.border.only(bottom=ft.BorderSide(1, p["glass_border"])),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=p["glass_shadow"],
                offset=ft.Offset(0, 3),
            ),
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Image(
                                src=resource_path("imagenes/logouce.png"),
                                width=34,
                                height=34,
                                fit=ft.ImageFit.CONTAIN,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "BuscadorApp",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=p["text_primary"],
                                    ),
                                    self.lbl_subtitulo_app,
                                ],
                                spacing=0,
                                tight=True,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        acciones_header,
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        kpis = _calcular_kpis_cache()
        self.kpi_cards = [
            self._crear_kpi_card(
                "Documentos Indexados",
                kpis["docs"],
                ft.Icons.FOLDER_COPY_ROUNDED,
                p["primary"],
            ),
            self._crear_kpi_card(
                "Universidades",
                kpis["universidades"],
                ft.Icons.ACCOUNT_BALANCE_ROUNDED,
                p["gold"],
            ),
            self._crear_kpi_card(
                "Programas",
                kpis["programas"],
                ft.Icons.SCHOOL_ROUNDED,
                p["success"],
            ),
            self._crear_kpi_card(
                "Docentes / Estudiantes",
                kpis["estudiantes"],
                ft.Icons.GROUPS_ROUNDED,
                "#8B5CF6",
            ),
        ]
        self.kpi_strip = ft.Container(
            visible=kpis["docs"] > 0,
            opacity=0.0,
            offset=ft.Offset(0, 0.03),
            animate_opacity=anim_smooth(300),
            animate_offset=anim_smooth(300),
            content=ft.Row(
                self.kpi_cards,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
                run_spacing=10,
                wrap=True,
            ),
        )

        self.card_docentes = self._crear_tarjeta_modulo(
            titulo="DOCENTES",
            descripcion="Consulta expedientes\nde doctorados y programas",
            icono=ft.Icons.SCHOOL_ROUNDED,
            color_acento=p["primary"],
            color_fondo_icono=p["primary_soft"],
            on_click=self.on_docentes,
        )

        self.card_oficios = self._crear_tarjeta_modulo(
            titulo="OFICIOS",
            descripcion="Gestiona oficios\ny documentación oficial",
            icono=ft.Icons.DESCRIPTION_ROUNDED,
            color_acento=p["danger"],
            color_fondo_icono=p["danger_soft"],
            on_click=self.on_oficios,
        )

        ahora = datetime.now()
        fecha_txt = ahora.strftime("%H:%M  •  %d/%m/%Y")
        saludo = _saludo_segun_hora()

        self.lbl_saludo = ft.Text(
            f"¡{saludo}, {self.nombre_usuario}!",
            size=34,
            weight=ft.FontWeight.BOLD,
            color=p["text_primary"],
            text_align=ft.TextAlign.CENTER,
        )

        centro = ft.Column(
            [
                self.lbl_saludo,
                ft.Text(
                    "Selecciona el módulo institucional que deseas consultar",
                    size=15,
                    color=p["text_secondary"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=4),
                self.kpi_strip,
                ft.Container(height=12),
                ft.Row(
                    [self.card_docentes, self.card_oficios],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=24,
                    run_spacing=20,
                    wrap=True,
                ),
                ft.Container(height=16),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=16, color=p["text_secondary"]),
                        ft.Text(fecha_txt, size=13, color=p["text_secondary"]),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
                ft.TextButton(
                    text="Acerca de la aplicación",
                    icon=ft.Icons.INFO_OUTLINE_ROUNDED,
                    style=ft.ButtonStyle(color=p["text_secondary"]),
                    on_click=lambda _: self.on_acerca_de(),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            expand=True,
        )

        return crear_fondo_ambiental(
            ft.Column(
                [
                    self.top_bar,
                    ft.Container(
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=24, vertical=16),
                        content=centro,
                        alignment=ft.alignment.center,
                    ),
                ],
                expand=True,
                spacing=0,
            ),
            palette=p,
        )

    def on_resize(self, width: float, height: float, update_ui: bool = True):
        if not self._activo:
            return
        mostrar_detalle = width >= 1080
        self.lbl_subtitulo_app.visible = mostrar_detalle
        self.lbl_nombre_usuario.visible = mostrar_detalle
        self.top_bar.padding = ft.padding.symmetric(horizontal=14 if width < 900 else 28)
        self.lbl_saludo.size = 26 if width < 900 else 34

        kpi_w = 165 if width < 1050 else 185
        for c in self.kpi_cards:
            c.width = kpi_w

        card_w = 310 if width < 1050 else 350
        self.card_docentes.width = card_w
        self.card_oficios.width = card_w
        if update_ui:
            self._safe_update()

    def on_mount(self, restoring: bool = False):
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)
        if self.kpi_strip.visible:
            self._timers.append(programar_timer(0.02, self._revelar_kpis))
        self._timers.append(programar_timer(0.05, lambda: self._revelar_tarjeta(self.card_docentes)))
        self._timers.append(programar_timer(0.14, lambda: self._revelar_tarjeta(self.card_oficios)))
        self._drive_monitor = DriveMonitor(self._on_drive_status)
        self._drive_monitor.start()

    def _revelar_kpis(self):
        if not self._activo:
            return
        self.kpi_strip.opacity = 1.0
        self.kpi_strip.offset = ft.Offset(0, 0)
        self._safe_update(self.kpi_strip)

    def _revelar_tarjeta(self, card: ft.Container):
        if not self._activo:
            return
        card.opacity = 1.0
        card.offset = ft.Offset(0, 0)
        self._safe_update(card)

    def _on_drive_status(self, conectado: bool):
        if not self._activo:
            return
        actualizar_badge_drive(self.badge_drive, self.icon_drive, self.txt_drive, conectado)
