"""
Vista de carga post-login en Flet responsive con tarjeta Glassmorphism y precalentamiento de caché.
"""
from datetime import datetime
import threading
from typing import Callable
import flet as ft

import config.settings as settings
from services.cache_service import get_cache
from ui_flet.theme import (
    anim_smooth,
    crear_avatar_iniciales,
    crear_fondo_ambiental,
    crear_glass_card,
    get_palette,
    get_viewport_size,
    programar_timer,
)


class LoadingView:
    """Pantalla intermedia tras el login que precalienta el caché antes de mostrar módulos."""

    def __init__(
        self,
        page: ft.Page,
        nombre_usuario: str,
        on_complete: Callable[[], None],
    ):
        self.page = page
        self.nombre_usuario = nombre_usuario
        self.on_complete = on_complete
        self._activo = True
        self._timers: list[threading.Timer] = []

        self.card_container: ft.Container
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
        p = get_palette()
        self.page.title = "BuscadorApp — Cargando Sistema..."

        ahora = datetime.now()
        fecha_txt = ahora.strftime("%H:%M:%S  •  %d/%m/%Y")

        self.progress = ft.ProgressBar(
            value=0.15,
            width=360,
            bar_height=7,
            border_radius=4,
            color=p["gold"],
            bgcolor=p["primary_soft"],
        )
        self.lbl_estado = ft.Text(
            "Inicializando módulos...",
            size=13,
            color=p["text_secondary"],
            text_align=ft.TextAlign.CENTER,
        )

        self.card_container = crear_glass_card(
            width=480,
            border_radius=22,
            padding=32,
            blur_sigma=18,
            opacity=0.0,
            scale=0.94,
            offset=ft.Offset(0, 0.04),
            animate_opacity=anim_smooth(320),
            animate_scale=anim_smooth(320),
            animate_offset=anim_smooth(320),
            content=ft.Column(
                [
                    crear_avatar_iniciales(self.nombre_usuario, size=70),
                    ft.Container(height=12),
                    ft.Text(
                        f"¡Bienvenido, {self.nombre_usuario}!",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=p["text_primary"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Sistema de Gestión de Expedientes • UCE",
                        size=14,
                        color=p["text_secondary"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=28, color=p["divider"]),
                    ft.Container(
                        bgcolor=p["surface_alt"],
                        border=ft.border.all(1, p["border"]),
                        border_radius=12,
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=18, color=p["primary"]),
                                ft.Text(
                                    fecha_txt,
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    color=p["text_secondary"],
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                    ),
                    ft.Container(height=16),
                    self.progress,
                    ft.Container(height=8),
                    self.lbl_estado,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True,
            ),
        )

        return crear_fondo_ambiental(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                padding=24,
                content=ft.Column(
                    [self.card_container],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            palette=p,
        )

    def on_resize(self, width: float, height: float, update_ui: bool = True):
        if not self._activo:
            return
        card_w = min(480, max(320, int(width - 48)))
        self.card_container.width = card_w
        self.progress.width = min(360, max(200, int(card_w - 72)))
        if update_ui:
            self._safe_update(self.card_container)

    def on_mount(self):
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)
        self._timers.append(programar_timer(0.04, self._animar_entrada))
        threading.Thread(target=self._precalentar_cache, daemon=True).start()
        self._timers.append(
            programar_timer(0.35, lambda: self._set_progreso(0.55, "Cargando caché de documentos..."))
        )
        self._timers.append(programar_timer(0.85, lambda: self._set_progreso(0.95, "¡Todo listo!")))
        self._timers.append(programar_timer(1.20, self._finalizar))

    def _animar_entrada(self):
        if not self._activo:
            return
        self.card_container.opacity = 1.0
        self.card_container.scale = 1.0
        self.card_container.offset = ft.Offset(0, 0)
        self._safe_update(self.card_container)

    def _set_progreso(self, valor: float, mensaje: str):
        if not self._activo:
            return
        self.progress.value = valor
        self.lbl_estado.value = mensaje
        self._safe_update(self.progress)
        self._safe_update(self.lbl_estado)

    def _precalentar_cache(self):
        try:
            if not settings.documentos_drive:
                cache = get_cache()
                if not cache.necesita_escaneo():
                    docs, _ = cache.obtener_documentos()
                    if docs:
                        settings.documentos_drive = docs
                        settings.documentos_cargados = True
        except Exception as e:
            print(f"[WARN] Precalentamiento de caché: {e}")

    def _finalizar(self):
        if not self._activo:
            return
        self.on_complete()
