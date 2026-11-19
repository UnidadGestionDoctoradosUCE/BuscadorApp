"""
Motor de tema dual (Claro / Oscuro con persistencia), Glassmorphism real y componentes compartidos.
Estética ejecutiva UCE: Azul Real Institucional + Oro Académico + Cristal Esmerilado.
"""
import os
import threading
from typing import Any, Callable, Optional
import flet as ft

import config.settings as settings
from ui_flet.services_bridge import (
    copiar_pdf_a_destino,
    crear_zip_multiple,
    verificar_drive_conectado,
)

# ==============================================================================
# PALETAS INSTITUCIONALES DUALES (Claro & Oscuro)
# ==============================================================================
LIGHT_PALETTE: dict[str, Any] = {
    "is_dark": False,
    "bg_app": "#EEF3F9",
    "bg_gradient": ["#F8FAFC", "#EEF3FA", "#E2ECF7"],
    "orb_primary": ft.Colors.with_opacity(0.14, "#1D4ED8"),
    "orb_gold": ft.Colors.with_opacity(0.11, "#C9A227"),
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "input_bg": "#F8FAFC",
    "glass_bg": ft.Colors.with_opacity(0.76, "#FFFFFF"),
    "glass_sidebar_bg": ft.Colors.with_opacity(0.84, "#FFFFFF"),
    "glass_border": ft.Colors.with_opacity(0.85, "#CBD5E1"),
    "glass_shadow": ft.Colors.with_opacity(0.08, "#0F172A"),
    "table_header": "#0F294A",
    "table_header_text": "#FFFFFF",
    "primary": "#0F3D75",
    "primary_dark": "#09264A",
    "primary_soft": "#DBEAFE",
    "gold": "#B88914",
    "gold_soft": "#FEF3C7",
    "success": "#059669",
    "success_dark": "#047857",
    "success_soft": "#D1FAE5",
    "danger": "#DC2626",
    "danger_soft": "#FEE2E2",
    "warning": "#D97706",
    "warning_soft": "#FEF3C7",
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#94A3B8",
    "border": "#CBD5E1",
    "divider": "#E2E8F0",
    "zebra_even": "#FFFFFF",
    "zebra_odd": "#F8FAFC",
    "row_hover": "#EFF6FF",
    "row_selected": "#DBEAFE",
}

DARK_PALETTE: dict[str, Any] = {
    "is_dark": True,
    "bg_app": "#070D19",
    "bg_gradient": ["#060B14", "#0B162B", "#101E38"],
    "orb_primary": ft.Colors.with_opacity(0.24, "#1D4ED8"),
    "orb_gold": ft.Colors.with_opacity(0.13, "#D4AF37"),
    "surface": "#0F1B30",
    "surface_alt": "#16243D",
    "input_bg": "#111E34",
    "glass_bg": ft.Colors.with_opacity(0.68, "#101D33"),
    "glass_sidebar_bg": ft.Colors.with_opacity(0.78, "#0D182B"),
    "glass_border": ft.Colors.with_opacity(0.16, "#FFFFFF"),
    "glass_shadow": ft.Colors.with_opacity(0.40, "#000000"),
    "table_header": "#13294B",
    "table_header_text": "#F8FAFC",
    "primary": "#38BDF8",
    "primary_dark": "#0284C7",
    "primary_soft": ft.Colors.with_opacity(0.18, "#38BDF8"),
    "gold": "#E5B946",
    "gold_soft": ft.Colors.with_opacity(0.16, "#E5B946"),
    "success": "#10B981",
    "success_dark": "#34D399",
    "success_soft": ft.Colors.with_opacity(0.18, "#10B981"),
    "danger": "#F87171",
    "danger_soft": ft.Colors.with_opacity(0.18, "#EF4444"),
    "warning": "#FBBF24",
    "warning_soft": ft.Colors.with_opacity(0.18, "#F59E0B"),
    "text_primary": "#F1F5F9",
    "text_secondary": "#CBD5E1",
    "text_muted": "#94A3B8",
    "border": ft.Colors.with_opacity(0.18, "#FFFFFF"),
    "divider": ft.Colors.with_opacity(0.12, "#FFFFFF"),
    "zebra_even": "#0E1A2E",
    "zebra_odd": "#132138",
    "row_hover": "#1A2E4D",
    "row_selected": "#1E3A63",
}

# Alias de compatibilidad
BG_APP = LIGHT_PALETTE["bg_app"]
BG_SURFACE = LIGHT_PALETTE["surface"]
BG_SIDEBAR = LIGHT_PALETTE["surface"]
BG_DARK = "#091529"
BG_TABLE_HEADER = LIGHT_PALETTE["table_header"]
PRIMARY = LIGHT_PALETTE["primary"]
PRIMARY_DARK = LIGHT_PALETTE["primary_dark"]
PRIMARY_LIGHT = LIGHT_PALETTE["primary_soft"]
ACCENT_BLUE = "#38BDF8"
ACCENT_GOLD = "#C9A227"
SUCCESS = LIGHT_PALETTE["success"]
SUCCESS_DARK = LIGHT_PALETTE["success_dark"]
SUCCESS_LIGHT = LIGHT_PALETTE["success_soft"]
DANGER = LIGHT_PALETTE["danger"]
DANGER_LIGHT = LIGHT_PALETTE["danger_soft"]
WARNING = LIGHT_PALETTE["warning"]
WARNING_LIGHT = LIGHT_PALETTE["warning_soft"]
TEXT_PRIMARY = LIGHT_PALETTE["text_primary"]
TEXT_SECONDARY = LIGHT_PALETTE["text_secondary"]
BORDER = LIGHT_PALETTE["border"]
ZEBRA_ODD = LIGHT_PALETTE["zebra_odd"]
ZEBRA_EVEN = LIGHT_PALETTE["zebra_even"]
ROW_SELECTED = LIGHT_PALETTE["row_selected"]
ROW_HOVER = LIGHT_PALETTE["row_hover"]

GRADIENT_DARK_HERO = ft.LinearGradient(
    begin=ft.alignment.top_left,
    end=ft.alignment.bottom_right,
    colors=["#071224", "#0F294A", "#173C6A"],
)


def is_dark_mode() -> bool:
    return getattr(settings, "theme", "light") == "dark"


def get_palette() -> dict[str, Any]:
    """Retorna la paleta activa según settings.theme ('light' o 'dark')."""
    return DARK_PALETTE if is_dark_mode() else LIGHT_PALETTE


def anim_smooth(ms: int = 280) -> ft.Animation:
    """Curva de animación suave para entradas, tarjetas y transiciones."""
    return ft.Animation(ms, ft.AnimationCurve.EASE_OUT_CUBIC)


def anim_fast(ms: int = 150) -> ft.Animation:
    """Curva de animación rápida para hover y micro-interacciones."""
    return ft.Animation(ms, ft.AnimationCurve.EASE_OUT)


def programar_timer(delay_seg: float, callback: Callable[[], None]) -> threading.Timer:
    """Crea e inicia un threading.Timer daemon y lo retorna para cancelación limpia."""
    timer = threading.Timer(delay_seg, callback)
    timer.daemon = True
    timer.start()
    return timer


def crear_fondo_ambiental(content: ft.Control, palette: Optional[dict[str, Any]] = None) -> ft.Container:
    """
    Envuelve la vista con gradiente institucional y orbes radiales sutiles
    para que los paneles glassmorphism reflejen profundidad real.
    """
    p = palette or get_palette()
    return ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=p["bg_gradient"],
        ),
        content=ft.Stack(
            [
                ft.Container(
                    left=-160,
                    top=-140,
                    width=520,
                    height=520,
                    border_radius=260,
                    gradient=ft.RadialGradient(
                        colors=[p["orb_primary"], ft.Colors.TRANSPARENT],
                    ),
                ),
                ft.Container(
                    right=-140,
                    bottom=-160,
                    width=500,
                    height=500,
                    border_radius=250,
                    gradient=ft.RadialGradient(
                        colors=[p["orb_gold"], ft.Colors.TRANSPARENT],
                    ),
                ),
                ft.Container(
                    right=220,
                    top=-120,
                    width=360,
                    height=360,
                    border_radius=180,
                    gradient=ft.RadialGradient(
                        colors=[p["orb_primary"], ft.Colors.TRANSPARENT],
                    ),
                ),
                ft.Container(expand=True, content=content),
            ],
            expand=True,
        ),
    )


def crear_glass_card(
    content: ft.Control,
    border_radius: int = 18,
    padding: Any = 24,
    width: Optional[int] = None,
    height: Optional[int] = None,
    expand: bool | int = False,
    blur_sigma: float = 16,
    is_sidebar: bool = False,
    border: Optional[ft.Border] = None,
    shadow: Optional[ft.BoxShadow] = None,
    **kwargs,
) -> ft.Container:
    """Crea una superficie Glassmorphism real usando ft.Blur + fondo translúcido."""
    p = get_palette()
    return ft.Container(
        content=content,
        width=width,
        height=height,
        expand=expand,
        padding=padding,
        border_radius=border_radius,
        blur=ft.Blur(blur_sigma, blur_sigma, ft.BlurTileMode.CLAMP),
        bgcolor=p["glass_sidebar_bg"] if is_sidebar else p["glass_bg"],
        border=border if border is not None else ft.border.all(1, p["glass_border"]),
        shadow=shadow
        if shadow is not None
        else ft.BoxShadow(
            spread_radius=0,
            blur_radius=24,
            color=p["glass_shadow"],
            offset=ft.Offset(0, 8),
        ),
        **kwargs,
    )


def crear_boton_tema(on_toggle: Callable[[], None], compact: bool = False) -> ft.Control:
    """Crea un botón elegante de cambio Claro/Oscuro acorde a la paleta actual."""
    p = get_palette()
    oscuro = p["is_dark"]
    icono = ft.Icons.LIGHT_MODE_ROUNDED if oscuro else ft.Icons.DARK_MODE_ROUNDED
    color_ico = p["gold"] if oscuro else p["primary"]
    tooltip = "Cambiar a modo claro" if oscuro else "Cambiar a modo oscuro"

    if compact:
        return ft.Container(
            border_radius=10,
            bgcolor=p["surface_alt"],
            border=ft.border.all(1, p["border"]),
            tooltip=tooltip,
            content=ft.IconButton(
                icon=icono,
                icon_color=color_ico,
                icon_size=18,
                on_click=lambda _: on_toggle(),
            ),
        )

    texto = "Modo Claro" if oscuro else "Modo Oscuro"
    return ft.OutlinedButton(
        text=texto,
        icon=icono,
        tooltip=tooltip,
        style=ft.ButtonStyle(
            color=p["text_primary"],
            icon_color=color_ico,
            bgcolor=p["surface_alt"],
            side=ft.BorderSide(1, p["border"]),
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        on_click=lambda _: on_toggle(),
    )


def crear_avatar_iniciales(
    nombre: str,
    size: int = 34,
    bgcolor: Optional[str] = None,
) -> ft.Container:
    """Crea un avatar circular con las iniciales del usuario/desarrollador."""
    p = get_palette()
    partes = [pt for pt in (nombre or "").strip().split() if pt]
    if len(partes) >= 2:
        iniciales = f"{partes[0][0]}{partes[1][0]}".upper()
    elif partes:
        iniciales = partes[0][:2].upper()
    else:
        iniciales = "U"

    return ft.Container(
        width=size,
        height=size,
        border_radius=size / 2,
        bgcolor=bgcolor or p["primary"],
        alignment=ft.alignment.center,
        content=ft.Text(
            iniciales,
            size=max(11, int(size * 0.38)),
            weight=ft.FontWeight.BOLD,
            color="#0B1120" if (bgcolor is None and p["is_dark"]) else ft.Colors.WHITE,
        ),
    )


def crear_chip_filtro_activo(
    etiqueta: str,
    valor: str,
    on_remove: Callable[[], None],
) -> ft.Container:
    """Crea un pill compacto con un filtro activo y botón × para limpiarlo."""
    p = get_palette()
    fg = p["primary"] if p["is_dark"] else p["primary_dark"]
    return ft.Container(
        bgcolor=p["primary_soft"],
        border=ft.border.all(1, ft.Colors.with_opacity(0.35, p["primary"])),
        border_radius=16,
        padding=ft.padding.only(left=10, right=4, top=3, bottom=3),
        content=ft.Row(
            [
                ft.Text(
                    f"{etiqueta}: {valor}",
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=fg,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Container(
                    border_radius=12,
                    padding=2,
                    ink=True,
                    on_click=lambda _: on_remove(),
                    tooltip=f"Quitar filtro {etiqueta}",
                    content=ft.Icon(
                        ft.Icons.CLOSE_ROUNDED,
                        size=14,
                        color=fg,
                    ),
                ),
            ],
            spacing=4,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


class FilePickerHelper:
    """
    Wrapper único de ft.FilePicker registrado una sola vez en page.overlay.
    Evita acumular múltiples FilePickers al navegar entre vistas o abrir diálogos.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self._callback: Optional[Callable[[Optional[str]], None]] = None
        self.picker = ft.FilePicker(on_result=self._on_result)
        self.page.overlay.append(self.picker)

    def _on_result(self, e: ft.FilePickerResultEvent):
        cb = self._callback
        self._callback = None
        if cb:
            cb(e.path)

    def save_file(
        self,
        callback: Callable[[Optional[str]], None],
        dialog_title: str = "Guardar archivo",
        file_name: str = "documento.pdf",
        allowed_extensions: Optional[list[str]] = None,
    ):
        self._callback = callback
        self.picker.save_file(
            dialog_title=dialog_title,
            file_name=file_name,
            allowed_extensions=allowed_extensions,
        )

    def get_directory_path(
        self,
        callback: Callable[[Optional[str]], None],
        dialog_title: str = "Seleccionar carpeta",
        initial_directory: Optional[str] = None,
    ):
        self._callback = callback
        self.picker.get_directory_path(
            dialog_title=dialog_title,
            initial_directory=initial_directory or None,
        )


def show_snackbar(page: ft.Page, mensaje: str, tipo: str = "info"):
    """Muestra una notificación flotante moderna usando page.open()."""
    p = get_palette()
    estilos = {
        "info": ("#0F3D75" if not p["is_dark"] else "#1E40AF", ft.Icons.INFO_OUTLINE_ROUNDED),
        "success": ("#047857", ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED),
        "warning": ("#B45309", ft.Icons.WARNING_AMBER_ROUNDED),
        "error": ("#B91C1C", ft.Icons.ERROR_OUTLINE_ROUNDED),
    }
    bgcolor, icon = estilos.get(tipo, estilos["info"])
    snack = ft.SnackBar(
        content=ft.Row(
            [
                ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                ft.Text(
                    mensaje,
                    color=ft.Colors.WHITE,
                    size=13,
                    weight=ft.FontWeight.W_500,
                    expand=True,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=bgcolor,
        behavior=ft.SnackBarBehavior.FLOATING,
        duration=3500,
        show_close_icon=True,
        close_icon_color=ft.Colors.WHITE,
    )
    try:
        page.open(snack)
    except Exception:
        pass


def get_viewport_size(page: ft.Page) -> tuple[float, float]:
    """Obtiene (ancho, alto) actuales del viewport de forma segura en cualquier contexto."""
    win = getattr(page, "window", None)
    w = getattr(page, "width", None) or getattr(win, "width", None) or 1280
    h = getattr(page, "height", None) or getattr(win, "height", None) or 760
    try:
        w = float(w)
    except Exception:
        w = 1280.0
    try:
        h = float(h)
    except Exception:
        h = 760.0
    return w, h


def show_info_dialog(page: ft.Page, titulo: str, mensaje: str, tipo: str = "info"):
    """Muestra un diálogo modal informativo adaptado al tema activo y tamaño de ventana."""
    p = get_palette()
    vp_w, vp_h = get_viewport_size(page)
    dlg_w = min(420, max(280, int(vp_w * 0.78)))
    icon_map = {
        "info": (ft.Icons.INFO_ROUNDED, p["primary"]),
        "success": (ft.Icons.CHECK_CIRCLE_ROUNDED, p["success"]),
        "warning": (ft.Icons.WARNING_ROUNDED, p["warning"]),
        "error": (ft.Icons.ERROR_ROUNDED, p["danger"]),
    }
    icon_name, icon_color = icon_map.get(tipo, icon_map["info"])
    txt_msg = ft.Text(mensaje, size=14, color=p["text_secondary"], selectable=True)
    content_ctrl = (
        ft.Container(
            width=dlg_w,
            height=max(180, int(vp_h * 0.50)),
            content=ft.Column([txt_msg], scroll=ft.ScrollMode.AUTO),
        )
        if len(mensaje) > 360
        else ft.Container(width=dlg_w, content=txt_msg)
    )

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=p["surface"],
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Row(
            [
                ft.Icon(icon_name, color=icon_color, size=26),
                ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, color=p["text_primary"], expand=True),
            ],
            spacing=10,
        ),
        content=content_ctrl,
        actions=[
            ft.ElevatedButton(
                text="Aceptar",
                bgcolor=p["primary"],
                color="#0B1120" if p["is_dark"] else ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda _: page.close(dlg),
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dlg)


def show_confirm_dialog(
    page: ft.Page,
    titulo: str,
    mensaje: str,
    on_confirm: Callable[[], None],
    confirm_text: str = "Confirmar",
    confirm_color: Optional[str] = None,
):
    """Muestra un diálogo modal de confirmación adaptado al tema activo y tamaño de ventana."""
    p = get_palette()
    vp_w, vp_h = get_viewport_size(page)
    dlg_w = min(420, max(280, int(vp_w * 0.78)))
    btn_color = confirm_color or p["primary"]
    txt_msg = ft.Text(mensaje, size=14, color=p["text_secondary"])
    content_ctrl = (
        ft.Container(
            width=dlg_w,
            height=max(180, int(vp_h * 0.50)),
            content=ft.Column([txt_msg], scroll=ft.ScrollMode.AUTO),
        )
        if len(mensaje) > 360
        else ft.Container(width=dlg_w, content=txt_msg)
    )

    def _confirmar(_):
        page.close(dlg)
        on_confirm()

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=p["surface"],
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Row(
            [
                ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, color=btn_color, size=26),
                ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, color=p["text_primary"], expand=True),
            ],
            spacing=10,
        ),
        content=content_ctrl,
        actions=[
            ft.OutlinedButton(
                text="Cancelar",
                style=ft.ButtonStyle(
                    color=p["text_secondary"],
                    side=ft.BorderSide(1, p["border"]),
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                on_click=lambda _: page.close(dlg),
            ),
            ft.ElevatedButton(
                text=confirm_text,
                bgcolor=btn_color,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=_confirmar,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dlg)


def crear_dropdown_filtro(
    label: str,
    opciones: list[str],
    on_change: Optional[Callable] = None,
    width: int = 310,
) -> ft.Dropdown:
    """Crea un Dropdown editable con búsqueda/filtrado instantáneo y alto contraste claro/oscuro."""
    p = get_palette()
    opts = [ft.dropdown.Option(key=op, text=op) for op in opciones]
    return ft.Dropdown(
        label=label,
        value="(Todos)" if "(Todos)" in opciones else (opciones[0] if opciones else None),
        options=opts,
        width=width,
        editable=True,
        enable_filter=True,
        enable_search=True,
        menu_height=260,
        border_radius=10,
        dense=True,
        text_size=13,
        color=p["text_primary"],
        text_style=ft.TextStyle(size=13, color=p["text_primary"]),
        label_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_600, color=p["text_secondary"]),
        border_color=p["border"],
        focused_border_color=p["primary"],
        bgcolor=p["surface"],
        fill_color=p["input_bg"],
        filled=True,
        on_change=on_change,
    )


def actualizar_dropdown_opciones(
    dropdown: ft.Dropdown,
    opciones: list[str],
    valor: str = "(Todos)",
    update_control: bool = True,
):
    """Repuebla de forma segura un Dropdown y restablece su valor seleccionado."""
    dropdown.options = [ft.dropdown.Option(key=op, text=op) for op in opciones]
    dropdown.value = valor if valor in opciones else (opciones[0] if opciones else None)
    if update_control:
        try:
            dropdown.update()
        except Exception:
            pass


def normalizar_valor_dropdown(valor: Optional[str]) -> str:
    """Convierte None o cadenas vacías del Dropdown editable a '(Todos)'."""
    if not valor or not str(valor).strip():
        return "(Todos)"
    return str(valor).strip()


def crear_badge_drive() -> tuple[ft.Container, ft.Icon, ft.Text]:
    """Crea el pill indicador de estado de Google Drive para la barra inferior / header."""
    p = get_palette()
    icono = ft.Icon(ft.Icons.CLOUD_SYNC_ROUNDED, size=14, color=p["warning"])
    texto = ft.Text("Verificando Drive...", size=12, weight=ft.FontWeight.W_600, color=p["warning"])
    badge = ft.Container(
        content=ft.Row([icono, texto], spacing=6, tight=True),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=20,
        bgcolor=p["warning_soft"],
        border=ft.border.all(1, ft.Colors.with_opacity(0.25, p["warning"])),
    )
    return badge, icono, texto


def actualizar_badge_drive(
    badge: ft.Container,
    icono: ft.Icon,
    texto: ft.Text,
    conectado: bool,
):
    """Actualiza el aspecto del pill de Drive según disponibilidad y paleta activa."""
    p = get_palette()
    if conectado:
        color = p["success_dark"]
        bg = p["success_soft"]
        icono.name = ft.Icons.CLOUD_DONE_ROUNDED
        texto.value = "Drive Montado"
    else:
        color = p["danger"]
        bg = p["danger_soft"]
        icono.name = ft.Icons.CLOUD_OFF_ROUNDED
        texto.value = "Drive Desconectado"

    icono.color = color
    texto.color = color
    badge.bgcolor = bg
    badge.border = ft.border.all(1, ft.Colors.with_opacity(0.25, color))
    try:
        badge.update()
    except Exception:
        pass


class DriveMonitor:
    """Verifica periódicamente cada 10s si las rutas de Google Drive están montadas."""

    def __init__(self, on_status: Callable[[bool], None], intervalo_seg: float = 10.0):
        self.on_status = on_status
        self.intervalo_seg = intervalo_seg
        self._activo = True
        self._timer: Optional[threading.Timer] = None

    def start(self):
        self._check_once()

    def _check_once(self):
        if not self._activo:
            return

        def _worker():
            if not self._activo:
                return
            conectado = verificar_drive_conectado()
            if not self._activo:
                return
            try:
                self.on_status(conectado)
            except Exception:
                pass
            if self._activo:
                self._timer = threading.Timer(self.intervalo_seg, self._check_once)
                self._timer.daemon = True
                self._timer.start()

        threading.Thread(target=_worker, daemon=True).start()

    def stop(self):
        self._activo = False
        if self._timer is not None:
            try:
                self._timer.cancel()
            except Exception:
                pass
            self._timer = None


def crear_paginador(
    on_prev: Callable,
    on_next: Callable,
) -> tuple[ft.Container, ft.Text, ft.IconButton, ft.IconButton]:
    """Crea la barra de paginación reutilizable al pie de las tablas."""
    p = get_palette()
    lbl_pagina = ft.Text("Página 1 de 1", size=12, weight=ft.FontWeight.W_600, color=p["text_secondary"])
    btn_prev = ft.IconButton(
        icon=ft.Icons.CHEVRON_LEFT_ROUNDED,
        tooltip="Página anterior",
        icon_color=p["text_primary"],
        icon_size=20,
        disabled=True,
        on_click=on_prev,
    )
    btn_next = ft.IconButton(
        icon=ft.Icons.CHEVRON_RIGHT_ROUNDED,
        tooltip="Página siguiente",
        icon_color=p["text_primary"],
        icon_size=20,
        disabled=True,
        on_click=on_next,
    )
    barra = ft.Container(
        visible=False,
        padding=ft.padding.symmetric(horizontal=14, vertical=4),
        border=ft.border.only(top=ft.BorderSide(1, p["divider"])),
        bgcolor=p["surface_alt"],
        content=ft.Row(
            [
                lbl_pagina,
                ft.Row([btn_prev, btn_next], spacing=2),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    )
    return barra, lbl_pagina, btn_prev, btn_next


def iniciar_descarga_archivos(
    page: ft.Page,
    file_picker: FilePickerHelper,
    rutas: list[str],
    nombre_zip_base: str = "Documentos_Filtrados",
):
    """Descarga 1 archivo PDF directamente o múltiples archivos comprimidos en un ZIP."""
    p = get_palette()
    if not rutas:
        show_snackbar(page, "Selecciona al menos un documento para descargar.", tipo="warning")
        return

    if len(rutas) == 1:
        ruta_unica = rutas[0]
        if not os.path.exists(ruta_unica):
            show_snackbar(page, "El archivo no existe o Drive no está disponible.", tipo="error")
            return

        def _on_save(dest: Optional[str]):
            if not dest:
                return
            ok, msg = copiar_pdf_a_destino(ruta_unica, dest)
            show_snackbar(page, msg, tipo="success" if ok else "error")

        file_picker.save_file(
            _on_save,
            dialog_title="Guardar archivo como",
            file_name=os.path.basename(ruta_unica),
            allowed_extensions=["pdf"],
        )
        return

    def _confirmar_zip():
        def _on_dir(carpeta: Optional[str]):
            if not carpeta:
                return
            show_snackbar(page, f"Comprimiendo {len(rutas)} archivo(s)...", tipo="info")

            def _worker():
                ok, res, count = crear_zip_multiple(rutas, carpeta, nombre_base=nombre_zip_base)
                if ok:
                    show_info_dialog(
                        page,
                        "Descarga completada",
                        f"Archivos comprimidos exitosamente en:\n{res}\n\nTotal incluidos: {count}",
                        tipo="success",
                    )
                else:
                    show_info_dialog(page, "Error al descargar", res, tipo="error")

            threading.Thread(target=_worker, daemon=True).start()

        file_picker.get_directory_path(
            _on_dir,
            dialog_title="Seleccionar carpeta para guardar el ZIP",
        )

    show_confirm_dialog(
        page,
        "Descargar múltiples documentos",
        f"¿Deseas descargar {len(rutas)} archivo(s) en un paquete ZIP?",
        _confirmar_zip,
        confirm_text="Descargar ZIP",
        confirm_color=p["primary"] if not p["is_dark"] else p["primary_dark"],
    )
