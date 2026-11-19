"""
Punto de entrada principal de BuscadorApp usando Flet (Flutter Desktop).
Incluye diseño responsive, Glassmorphism, transiciones con AnimatedSwitcher
y modo Claro/Oscuro dinámico con persistencia.
"""
import os
import threading
from typing import Optional
import flet as ft

import config.settings as settings
from ui_flet.theme import (
    DARK_PALETTE,
    LIGHT_PALETTE,
    FilePickerHelper,
    get_palette,
    get_viewport_size,
)
from ui_flet.views.acerca_de_view import AcercaDeView
from ui_flet.views.docentes_view import DocentesView
from ui_flet.views.loading_view import LoadingView
from ui_flet.views.login_view import LoginView
from ui_flet.views.oficios_view import OficiosView
from ui_flet.views.selection_view import SelectionView
from ui_flet.views.splash_view import SplashView
from utils.file_utils import resource_path


class AppFlet:
    """Controlador principal de navegación, responsive layout, transiciones y tema dinámico."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_view = None
        self._current_route = "splash"
        self._view_seq = 0
        self._resize_timer: Optional[threading.Timer] = None
        self.file_picker = FilePickerHelper(page)

        self.page.on_keyboard_event = self._on_keyboard
        self.page.on_resized = self._on_resized

        self.switcher = ft.AnimatedSwitcher(
            content=ft.Container(expand=True),
            expand=True,
            duration=280,
            reverse_duration=180,
            switch_in_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            switch_out_curve=ft.AnimationCurve.EASE_IN_CUBIC,
            transition=ft.AnimatedSwitcherTransition.FADE,
        )
        self.page.add(self.switcher)

    def _on_keyboard(self, e: ft.KeyboardEvent):
        if self.current_view and hasattr(self.current_view, "handle_keyboard"):
            self.current_view.handle_keyboard(e)

    def _on_resized(self, _=None):
        if self._resize_timer:
            try:
                self._resize_timer.cancel()
            except Exception:
                pass
        self._resize_timer = threading.Timer(0.08, self._aplicar_resize)
        self._resize_timer.daemon = True
        self._resize_timer.start()

    def _aplicar_resize(self):
        vista = self.current_view
        if vista and hasattr(vista, "on_resize"):
            w, h = get_viewport_size(self.page)
            try:
                vista.on_resize(w, h, update_ui=True)
            except TypeError:
                vista.on_resize(w, h)
            except Exception:
                pass

    def _montar_vista(self, vista, route: str, state: Optional[dict] = None):
        if self.current_view and hasattr(self.current_view, "dispose"):
            try:
                self.current_view.dispose()
            except Exception:
                pass
        self.current_view = vista
        self._current_route = route
        self._view_seq += 1

        self.switcher.content = ft.Container(
            key=f"view-{self._view_seq}",
            expand=True,
            content=vista.build(),
        )
        restored = False
        if state and hasattr(vista, "restore_state"):
            try:
                vista.restore_state(state)
                restored = True
            except Exception as e:
                print(f"[WARN] Error restaurando estado en {route}: {e}")

        if hasattr(vista, "on_resize"):
            w, h = get_viewport_size(self.page)
            try:
                vista.on_resize(w, h, update_ui=False)
            except TypeError:
                vista.on_resize(w, h)
            except Exception:
                pass

        try:
            self.switcher.update()
            self.page.update()
        except Exception:
            pass

        if hasattr(vista, "on_mount"):
            try:
                vista.on_mount(restoring=restored)
            except TypeError:
                vista.on_mount()

    def set_theme(self, nuevo_tema: str):
        """Aplica dinámicamente el tema Claro/Oscuro, lo persiste y preserva el estado de la vista actual."""
        tema = "dark" if nuevo_tema == "dark" else "light"
        settings.guardar_tema(tema)

        self.page.theme_mode = ft.ThemeMode.DARK if tema == "dark" else ft.ThemeMode.LIGHT
        self.page.bgcolor = get_palette()["bg_app"]

        state = None
        if self.current_view and hasattr(self.current_view, "get_state"):
            try:
                state = self.current_view.get_state()
            except Exception:
                state = None

        route = self._current_route
        if route == "login":
            self.mostrar_login(state=state)
        elif route == "selection":
            self.mostrar_seleccion(state=state)
        elif route == "docentes":
            self.mostrar_docentes(state=state)
        elif route == "oficios":
            self.mostrar_oficios(state=state)
        elif route == "acerca_de":
            self.mostrar_acerca_de(state=state)
        else:
            try:
                self.page.update()
            except Exception:
                pass

    def toggle_theme(self):
        nuevo = "light" if settings.theme == "dark" else "dark"
        self.set_theme(nuevo)

    def mostrar_splash(self):
        self._montar_vista(
            SplashView(self.page, on_complete=self.mostrar_login),
            route="splash",
        )

    def mostrar_login(self, state: Optional[dict] = None):
        self._montar_vista(
            LoginView(
                self.page,
                self.on_login_success,
                on_toggle_theme=self.toggle_theme,
            ),
            route="login",
            state=state,
        )

    def on_login_success(self, nombre_usuario: str):
        settings.nombre_usuario_actual = nombre_usuario
        self.mostrar_carga(nombre_usuario)

    def mostrar_carga(self, nombre_usuario: str):
        self._montar_vista(
            LoadingView(
                self.page,
                nombre_usuario,
                on_complete=lambda: self.mostrar_seleccion(nombre_usuario),
            ),
            route="loading",
        )

    def mostrar_seleccion(self, nombre_usuario: Optional[str] = None, state: Optional[dict] = None):
        usuario = nombre_usuario or settings.nombre_usuario_actual or "Usuario"
        self._montar_vista(
            SelectionView(
                self.page,
                self.file_picker,
                usuario,
                on_docentes=self.mostrar_docentes,
                on_oficios=self.mostrar_oficios,
                on_acerca_de=self.mostrar_acerca_de,
                on_cerrar_sesion=self.cerrar_sesion,
                on_toggle_theme=self.toggle_theme,
                on_set_theme=self.set_theme,
            ),
            route="selection",
            state=state,
        )

    def mostrar_docentes(self, state: Optional[dict] = None):
        self._montar_vista(
            DocentesView(
                self.page,
                self.file_picker,
                on_volver=lambda: self.mostrar_seleccion(),
                on_cerrar_sesion=self.cerrar_sesion,
                on_toggle_theme=self.toggle_theme,
            ),
            route="docentes",
            state=state,
        )

    def mostrar_oficios(self, state: Optional[dict] = None):
        self._montar_vista(
            OficiosView(
                self.page,
                self.file_picker,
                on_volver=lambda: self.mostrar_seleccion(),
                on_cerrar_sesion=self.cerrar_sesion,
                on_toggle_theme=self.toggle_theme,
            ),
            route="oficios",
            state=state,
        )

    def mostrar_acerca_de(self, state: Optional[dict] = None):
        self._montar_vista(
            AcercaDeView(
                self.page,
                on_volver=lambda: self.mostrar_seleccion(),
                on_toggle_theme=self.toggle_theme,
            ),
            route="acerca_de",
            state=state,
        )

    def cerrar_sesion(self):
        settings.nombre_usuario_actual = ""
        self.mostrar_login()


def main(page: ft.Page):
    """Configura la ventana de escritorio con el tema persistido e inicia la aplicación."""
    settings.cargar_configuracion()
    tema_inicial = settings.theme if settings.theme in ("light", "dark") else "light"

    page.title = "BuscadorApp — Gestión de Doctorados y Oficios"
    page.theme_mode = ft.ThemeMode.DARK if tema_inicial == "dark" else ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=LIGHT_PALETTE["primary"], font_family="Segoe UI")
    page.dark_theme = ft.Theme(color_scheme_seed=DARK_PALETTE["primary"], font_family="Segoe UI")
    page.padding = 0
    page.bgcolor = get_palette()["bg_app"]
    page.window.maximized = True
    page.window.min_width = 760
    page.window.min_height = 560

    icon_path = resource_path("imagenes/logouce.png")
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    app = AppFlet(page)
    app.mostrar_splash()


if __name__ == "__main__":
    ft.app(target=main)
