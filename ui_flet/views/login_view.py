"""
Vista de inicio de sesión ejecutiva y responsive en Flet:
- Panel izquierdo institucional adaptativo (oculto en ventanas < 960px con header compacto en la tarjeta)
- Panel derecho con fondo ambiental, selector de tema Claro/Oscuro y tarjeta Glassmorphism
"""
import threading
from typing import Callable, Optional
import flet as ft

import config.settings as settings
from ui_flet.services_bridge import verificar_credenciales_flet
from ui_flet.theme import (
    ACCENT_BLUE,
    ACCENT_GOLD,
    GRADIENT_DARK_HERO,
    anim_fast,
    anim_smooth,
    crear_boton_tema,
    crear_fondo_ambiental,
    crear_glass_card,
    get_palette,
    get_viewport_size,
    programar_timer,
)
from utils.file_utils import resource_path


class LoginView:
    """Vista de autenticación responsive de dos paneles con glassmorphism y tema dinámico."""

    def __init__(
        self,
        page: ft.Page,
        on_login_success: Callable[[str], None],
        on_toggle_theme: Optional[Callable[[], None]] = None,
    ):
        self.page = page
        self.on_login_success = on_login_success
        self.on_toggle_theme = on_toggle_theme
        self._activo = True
        self._timers: list[threading.Timer] = []

        self.panel_izquierdo: ft.Container
        self.compact_brand: ft.Container
        self.txt_usuario: ft.TextField
        self.txt_contra: ft.TextField
        self.lbl_error: ft.Text
        self.box_error: ft.Container
        self.btn_ingresar: ft.ElevatedButton
        self.card_form: ft.Container

    def dispose(self):
        self._activo = False
        for t in self._timers:
            try:
                t.cancel()
            except Exception:
                pass
        self._timers.clear()

    def get_state(self) -> dict:
        return {"usuario": self.txt_usuario.value or ""}

    def restore_state(self, state: dict):
        if not state:
            return
        if state.get("usuario"):
            self.txt_usuario.value = state["usuario"]
            self._safe_update(self.txt_usuario)

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
        self.page.title = "Unidad Administrativa de Gestión de Doctorados - Login"

        logo_halo = ft.Container(
            width=156,
            height=156,
            border_radius=78,
            blur=ft.Blur(16, 16, ft.BlurTileMode.CLAMP),
            bgcolor=ft.Colors.with_opacity(0.09, ft.Colors.WHITE),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.45, ACCENT_GOLD)),
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=28,
                color=ft.Colors.with_opacity(0.24, ACCENT_BLUE),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Image(
                src=resource_path("imagenes/logouce.png"),
                width=120,
                height=120,
                fit=ft.ImageFit.CONTAIN,
            ),
        )

        self.panel_izquierdo = ft.Container(
            width=420,
            visible=True,
            gradient=GRADIENT_DARK_HERO,
            border=ft.border.only(right=ft.BorderSide(2, ft.Colors.with_opacity(0.45, ACCENT_GOLD))),
            content=ft.Stack(
                [
                    ft.Container(
                        left=-100,
                        top=-100,
                        width=320,
                        height=320,
                        border_radius=160,
                        gradient=ft.RadialGradient(
                            colors=[ft.Colors.with_opacity(0.20, ACCENT_BLUE), ft.Colors.TRANSPARENT],
                        ),
                    ),
                    ft.Container(
                        right=-90,
                        bottom=-90,
                        width=320,
                        height=320,
                        border_radius=160,
                        gradient=ft.RadialGradient(
                            colors=[ft.Colors.with_opacity(0.16, ACCENT_GOLD), ft.Colors.TRANSPARENT],
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        padding=36,
                        content=ft.Column(
                            [
                                logo_halo,
                                ft.Container(height=20),
                                ft.Text(
                                    "UNIVERSIDAD",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=ACCENT_BLUE,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    "CENTRAL",
                                    size=26,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    "DEL ECUADOR",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=ACCENT_BLUE,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(
                                    width=84,
                                    height=3,
                                    bgcolor=ACCENT_GOLD,
                                    border_radius=2,
                                    margin=ft.margin.symmetric(vertical=20),
                                ),
                                ft.Text(
                                    "Unidad Administrativa de Gestión de Doctorados",
                                    size=13,
                                    color="#CBD5E1",
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(height=24),
                                ft.Container(
                                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                                    border=ft.border.all(1, ft.Colors.with_opacity(0.28, ACCENT_GOLD)),
                                    border_radius=20,
                                    padding=ft.padding.symmetric(horizontal=16, vertical=6),
                                    content=ft.Row(
                                        [
                                            ft.Icon(ft.Icons.SHIELD_OUTLINED, size=14, color=ACCENT_GOLD),
                                            ft.Text(
                                                "v2.0 • Portal Institucional",
                                                size=11,
                                                weight=ft.FontWeight.W_600,
                                                color="#E2E8F0",
                                            ),
                                        ],
                                        spacing=6,
                                        tight=True,
                                    ),
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=4,
                            expand=True,
                        ),
                    ),
                ],
                expand=True,
            ),
        )

        self.compact_brand = ft.Container(
            visible=False,
            padding=ft.padding.only(bottom=6),
            content=ft.Row(
                [
                    ft.Image(
                        src=resource_path("imagenes/logouce.png"),
                        width=40,
                        height=40,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "Universidad Central del Ecuador",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=p["text_primary"],
                            ),
                            ft.Text(
                                "Portal Institucional • v2.0",
                                size=11,
                                color=p["text_secondary"],
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

        self.lbl_error = ft.Text("", size=13, color=p["danger"], expand=True)
        self.box_error = ft.Container(
            visible=False,
            opacity=0.0,
            animate_opacity=anim_fast(180),
            bgcolor=p["danger_soft"],
            border=ft.border.all(1, ft.Colors.with_opacity(0.45, p["danger"])),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=p["danger"], size=18),
                    self.lbl_error,
                ],
                spacing=8,
            ),
        )

        self.txt_usuario = ft.TextField(
            label="Usuario",
            hint_text="Ingresa tu usuario",
            prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            autofocus=True,
            border_radius=10,
            border_color=p["border"],
            focused_border_color=p["primary"],
            bgcolor=p["input_bg"],
            filled=True,
            color=p["text_primary"],
            cursor_color=p["primary"],
            hint_style=ft.TextStyle(color=p["text_muted"]),
            label_style=ft.TextStyle(color=p["text_secondary"]),
            text_size=14,
            on_submit=lambda _: self.txt_contra.focus(),
            on_change=lambda _: self._ocultar_error(),
        )

        self.txt_contra = ft.TextField(
            label="Contraseña",
            hint_text="Ingresa tu contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            border_color=p["border"],
            focused_border_color=p["primary"],
            bgcolor=p["input_bg"],
            filled=True,
            color=p["text_primary"],
            cursor_color=p["primary"],
            hint_style=ft.TextStyle(color=p["text_muted"]),
            label_style=ft.TextStyle(color=p["text_secondary"]),
            text_size=14,
            on_submit=self._intentar_login,
            on_change=lambda _: self._ocultar_error(),
        )

        self.btn_ingresar = ft.ElevatedButton(
            text="INGRESAR",
            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
            bgcolor=p["primary"],
            color="#0B1120" if p["is_dark"] else ft.Colors.WHITE,
            height=48,
            expand=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
            ),
            on_click=self._intentar_login,
        )

        self.card_form = crear_glass_card(
            width=450,
            border_radius=22,
            padding=32,
            blur_sigma=18,
            opacity=0.0,
            offset=ft.Offset(0, 0.04),
            animate_opacity=anim_smooth(320),
            animate_offset=anim_smooth(320),
            content=ft.Column(
                [
                    self.compact_brand,
                    ft.Row(
                        [
                            ft.Container(
                                width=38,
                                height=4,
                                bgcolor=p["gold"],
                                border_radius=2,
                            ),
                            ft.Text(
                                "ACCESO AUTORIZADO",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=p["gold"],
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        "BIENVENIDO",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=p["text_primary"],
                    ),
                    ft.Text(
                        "Unidad de Gestión de Doctorados",
                        size=15,
                        color=p["text_secondary"],
                    ),
                    ft.Container(height=10),
                    self.txt_usuario,
                    self.txt_contra,
                    self.box_error,
                    ft.Container(height=4),
                    ft.Row([self.btn_ingresar]),
                    ft.Divider(height=24, color=p["divider"]),
                    ft.Column(
                        [
                            ft.Text(
                                "Sistema de Gestión de Expedientes",
                                size=12,
                                color=p["text_secondary"],
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "© Universidad Central del Ecuador",
                                size=11,
                                color=p["text_muted"],
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                ],
                spacing=10,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

        btn_tema_corner = (
            ft.Container(
                top=16,
                right=20,
                content=crear_boton_tema(self.on_toggle_theme, compact=False),
            )
            if self.on_toggle_theme
            else ft.Container()
        )

        panel_derecho = crear_fondo_ambiental(
            ft.Stack(
                [
                    ft.Container(
                        expand=True,
                        alignment=ft.alignment.center,
                        padding=24,
                        content=ft.Column(
                            [self.card_form],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                    ),
                    btn_tema_corner,
                ],
                expand=True,
            ),
            palette=p,
        )

        return ft.Row(
            [self.panel_izquierdo, panel_derecho],
            spacing=0,
            expand=True,
        )

    def on_resize(self, width: float, height: float, update_ui: bool = True):
        if not self._activo:
            return
        if width < 960:
            self.panel_izquierdo.visible = False
            self.compact_brand.visible = True
            avail_w = width
        elif width < 1160:
            self.panel_izquierdo.visible = True
            self.panel_izquierdo.width = 340
            self.compact_brand.visible = False
            avail_w = width - 340
        else:
            self.panel_izquierdo.visible = True
            self.panel_izquierdo.width = 420
            self.compact_brand.visible = False
            avail_w = width - 420

        self.card_form.width = min(450, max(320, int(avail_w - 40)))
        if update_ui:
            self._safe_update()

    def on_mount(self, restoring: bool = False):
        w, h = get_viewport_size(self.page)
        self.on_resize(w, h, update_ui=True)
        self._timers.append(programar_timer(0.04, self._animar_entrada))

    def _animar_entrada(self):
        if not self._activo:
            return
        self.card_form.opacity = 1.0
        self.card_form.offset = ft.Offset(0, 0)
        self._safe_update(self.card_form)

    def _ocultar_error(self):
        if self.box_error.visible:
            self.box_error.opacity = 0.0
            self.box_error.visible = False
            self._safe_update(self.box_error)

    def _mostrar_error(self, mensaje: str):
        self.lbl_error.value = mensaje
        self.box_error.visible = True
        self.box_error.opacity = 1.0
        self._safe_update(self.box_error)

    def _intentar_login(self, _=None):
        if not self._activo:
            return
        usuario = (self.txt_usuario.value or "").strip()
        contrasena = (self.txt_contra.value or "").strip()

        if not usuario or not contrasena:
            self._mostrar_error("Debes ingresar usuario y contraseña.")
            return

        self.btn_ingresar.disabled = True
        self.btn_ingresar.text = "VERIFICANDO..."
        self._safe_update(self.btn_ingresar)

        valido, nombre_real, error_msg = verificar_credenciales_flet(usuario, contrasena)
        if not self._activo:
            return

        if valido and nombre_real:
            settings.nombre_usuario_actual = nombre_real
            self.on_login_success(nombre_real)
        else:
            self.btn_ingresar.disabled = False
            self.btn_ingresar.text = "INGRESAR"
            self._safe_update(self.btn_ingresar)
            self._mostrar_error(error_msg or "Usuario o contraseña incorrectos.")
