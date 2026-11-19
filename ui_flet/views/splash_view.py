"""
Splash Screen inicial en Flet responsive con gradiente institucional, orbes dorados/azules y aro glassmorphism.
"""
import threading
from typing import Callable
import flet as ft

import config.settings as settings
from ui_flet.theme import (
    ACCENT_BLUE,
    ACCENT_GOLD,
    GRADIENT_DARK_HERO,
    anim_smooth,
    get_viewport_size,
    programar_timer,
)
from utils.file_utils import resource_path
from utils.path_utils import encontrar_rutas_drive


class SplashView:
    """Pantalla de arranque inicial mientras se detectan rutas de Google Drive."""

    def __init__(self, page: ft.Page, on_complete: Callable[[], None]):
        self.page = page
        self.on_complete = on_complete
        self._activo = True
        self._timers: list[threading.Timer] = []

        self.logo_halo: ft.Container
        self.logo_img: ft.Image
        self.hero_box: ft.Container
        self.progress: ft.ProgressBar
        self.lbl_estado: ft.Text

    def dispose(self):
        self._activo = False
        for t in self._timers:
            try:
                t.cancel()
            except Exception:
                pass
        self._timers.clear()

    def _safe_update(self, control: ft.Control | None = None):
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
        self.page.title = "BuscadorApp — Iniciando..."

        self.logo_img = ft.Image(
            src=resource_path("imagenes/logouce3.png"),
            width=128,
            height=128,
            fit=ft.ImageFit.CONTAIN,
        )
        self.logo_halo = ft.Container(
            width=174,
            height=174,
            border_radius=87,
            blur=ft.Blur(18, 18, ft.BlurTileMode.CLAMP),
            bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.40, ACCENT_GOLD)),
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=4,
                blur_radius=34,
                color=ft.Colors.with_opacity(0.26, ACCENT_BLUE),
                offset=ft.Offset(0, 6),
            ),
            content=self.logo_img,
        )

        self.progress = ft.ProgressBar(
            value=0.1,
            width=320,
            bar_height=6,
            border_radius=4,
            color=ACCENT_GOLD,
            bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
        )
        self.lbl_estado = ft.Text(
            "Inicializando aplicación...",
            size=13,
            color="#CBD5E1",
            text_align=ft.TextAlign.CENTER,
        )

        self.hero_box = ft.Container(
            opacity=0.0,
            scale=0.88,
            animate_opacity=anim_smooth(450),
            animate_scale=anim_smooth(450),
            padding=24,
            content=ft.Column(
                [
                    self.logo_halo,
                    ft.Container(height=20),
                    ft.Text(
                        "BuscadorApp",
                        size=36,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Sistema de Gestión Documental • UCE",
                        size=15,
                        color="#CBD5E1",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        width=84,
                        height=3,
                        bgcolor=ACCENT_GOLD,
                        border_radius=2,
                        margin=ft.margin.symmetric(vertical=16),
                    ),
                    self.progress,
                    ft.Container(height=8),
                    self.lbl_estado,
                    ft.Container(height=14),
                    ft.Text(
                        "v2.0 • Portal Institucional • Universidad Central del Ecuador",
                        size=11,
                        color="#94A3B8",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                spacing=4,
            ),
        )

        return ft.Container(
            expand=True,
            gradient=GRADIENT_DARK_HERO,
            content=ft.Stack(
                [
                    ft.Container(
                        left=-140,
                        top=-140,
                        width=440,
                        height=440,
                        border_radius=220,
                        gradient=ft.RadialGradient(
                            colors=[ft.Colors.with_opacity(0.24, ACCENT_BLUE), ft.Colors.TRANSPARENT],
                        ),
                    ),
                    ft.Container(
                        right=-110,
                        bottom=-120,
                        width=440,
                        height=440,
                        border_radius=220,
                        gradient=ft.RadialGradient(
                            colors=[ft.Colors.with_opacity(0.18, ACCENT_GOLD), ft.Colors.TRANSPARENT],
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.alignment.center,
                        content=self.hero_box,
                    ),
                ],
                expand=True,
            ),
        )

    def on_resize(self, width: float, height: float, update_ui: bool = True):
        if not self._activo:
            return
        compacto = height < 640
        halo_size = 136 if compacto else 174
        img_size = 98 if compacto else 128

        self.logo_halo.width = halo_size
        self.logo_halo.height = halo_size
        self.logo_halo.border_radius = halo_size / 2
        self.logo_img.width = img_size
        self.logo_img.height = img_size
        self.progress.width = min(320, max(200, int(width - 80)))
        if update_ui:
            self._safe_update(self.hero_box)

    def on_mount(self):
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)
        self._timers.append(programar_timer(0.05, self._animar_entrada))
        threading.Thread(target=self._detectar_rutas_bg, daemon=True).start()
        self._timers.append(
            programar_timer(0.25, lambda: self._set_progreso(0.28, "Buscando unidades de Google Drive..."))
        )
        self._timers.append(
            programar_timer(0.85, lambda: self._set_progreso(0.68, "Cargando configuración del sistema..."))
        )
        self._timers.append(programar_timer(1.30, lambda: self._set_progreso(1.0, "¡Listo!")))
        self._timers.append(programar_timer(1.55, self._finalizar))

    def _animar_entrada(self):
        if not self._activo:
            return
        self.hero_box.opacity = 1.0
        self.hero_box.scale = 1.0
        self._safe_update(self.hero_box)

    def _set_progreso(self, valor: float, mensaje: str):
        if not self._activo:
            return
        self.progress.value = valor
        self.lbl_estado.value = mensaje
        self._safe_update(self.progress)
        self._safe_update(self.lbl_estado)

    def _detectar_rutas_bg(self):
        try:
            if not settings.ruta_doctorados or not settings.ruta_oficios or not settings.ruta_doctorados2:
                r_doc, r_of, r_doc2 = encontrar_rutas_drive()
                if not settings.ruta_doctorados:
                    settings.ruta_doctorados = r_doc
                if not settings.ruta_oficios:
                    settings.ruta_oficios = r_of
                if not settings.ruta_doctorados2:
                    settings.ruta_doctorados2 = r_doc2
        except Exception as e:
            print(f"[WARN] Error detectando rutas en splash: {e}")

    def _finalizar(self):
        if not self._activo:
            return
        self.on_complete()
