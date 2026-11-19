"""
Diálogo modal de Configuración para la interfaz Flet.
Permite ajustar rutas de Google Drive, validar si existen, auto-detectarlas y elegir Modo Claro/Oscuro.
"""
import os
from typing import Callable, Optional
import flet as ft

import config.settings as settings
from services.cache_service import get_cache
from ui_flet.theme import (
    FilePickerHelper,
    get_palette,
    get_viewport_size,
    show_snackbar,
)
from utils.path_utils import encontrar_rutas_drive


def abrir_config_dialog(
    page: ft.Page,
    file_picker: FilePickerHelper,
    on_saved: Optional[Callable[[], None]] = None,
    on_theme_change: Optional[Callable[[str], None]] = None,
    valores_iniciales: Optional[tuple[str, str, str]] = None,
):
    """Abre un AlertDialog modal responsive para configurar rutas de Google Drive y Apariencia."""
    p = get_palette()
    vp_w, vp_h = get_viewport_size(page)
    dlg_w = min(640, max(360, int(vp_w * 0.84)))
    doc1_init, doc2_init, ofi_init = valores_iniciales or (
        settings.ruta_doctorados or "",
        settings.ruta_doctorados2 or "",
        settings.ruta_oficios or "",
    )
    tema_seleccionado = ["dark" if p["is_dark"] else "light"]

    def _crear_indicador(ruta: str) -> ft.Icon:
        existe = bool(ruta and os.path.exists(ruta.strip()))
        return ft.Icon(
            name=ft.Icons.CHECK_CIRCLE_ROUNDED if existe else ft.Icons.WARNING_AMBER_ROUNDED,
            color=p["success_dark"] if existe else p["warning"],
            size=20,
            tooltip="Directorio accesible en disco" if existe else "Ruta no encontrada o vacía",
        )

    def _refrescar_indicador(campo: ft.TextField, icono: ft.Icon, update_ctrl: bool = True):
        ruta = (campo.value or "").strip()
        existe = bool(ruta and os.path.exists(ruta))
        icono.name = ft.Icons.CHECK_CIRCLE_ROUNDED if existe else ft.Icons.WARNING_AMBER_ROUNDED
        icono.color = p["success_dark"] if existe else p["warning"]
        icono.tooltip = "Directorio accesible en disco" if existe else "Ruta no encontrada o vacía"
        if update_ctrl:
            try:
                icono.update()
            except Exception:
                pass

    ico_doc1 = _crear_indicador(doc1_init)
    ico_doc2 = _crear_indicador(doc2_init)
    ico_ofi = _crear_indicador(ofi_init)

    def _crear_campo_ruta(label: str, valor: str, icono: ft.Icon) -> ft.TextField:
        return ft.TextField(
            label=label,
            value=valor,
            expand=True,
            dense=True,
            text_size=13,
            color=p["text_primary"],
            cursor_color=p["primary"],
            label_style=ft.TextStyle(size=12, color=p["text_secondary"]),
            border_radius=10,
            border_color=p["border"],
            focused_border_color=p["primary"],
            bgcolor=p["input_bg"],
            filled=True,
            suffix=icono,
        )

    txt_doc1 = _crear_campo_ruta("Ruta Doctorados UCE (DB General)", doc1_init, ico_doc1)
    txt_doc2 = _crear_campo_ruta("Ruta Doctorados 2 (DB General 2)", doc2_init, ico_doc2)
    txt_ofi = _crear_campo_ruta("Ruta Oficios (DB General Oficios)", ofi_init, ico_ofi)

    txt_doc1.on_change = lambda _: _refrescar_indicador(txt_doc1, ico_doc1)
    txt_doc2.on_change = lambda _: _refrescar_indicador(txt_doc2, ico_doc2)
    txt_ofi.on_change = lambda _: _refrescar_indicador(txt_ofi, ico_ofi)

    def _examinar(campo: ft.TextField, icono: ft.Icon, titulo: str):
        def _on_dir(path: Optional[str]):
            if path:
                campo.value = os.path.normpath(path)
                _refrescar_indicador(campo, icono, update_ctrl=False)
                try:
                    campo.update()
                except Exception:
                    pass

        inicial = campo.value.strip() if campo.value and os.path.isdir(campo.value.strip()) else None
        file_picker.get_directory_path(_on_dir, dialog_title=titulo, initial_directory=inicial)

    def _fila_ruta(campo: ft.TextField, icono: ft.Icon, titulo_picker: str) -> ft.Row:
        return ft.Row(
            [
                campo,
                ft.ElevatedButton(
                    text="Examinar",
                    icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                    bgcolor=p["primary"],
                    color="#0B1120" if p["is_dark"] else ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    ),
                    on_click=lambda _, c=campo, i=icono, t=titulo_picker: _examinar(c, i, t),
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _autodetectar(_):
        r_doc, r_of, r_doc2 = encontrar_rutas_drive()
        detectadas = 0
        if r_doc:
            txt_doc1.value = r_doc
            detectadas += 1
        if r_doc2:
            txt_doc2.value = r_doc2
            detectadas += 1
        if r_of:
            txt_ofi.value = r_of
            detectadas += 1

        _refrescar_indicador(txt_doc1, ico_doc1, update_ctrl=False)
        _refrescar_indicador(txt_doc2, ico_doc2, update_ctrl=False)
        _refrescar_indicador(txt_ofi, ico_ofi, update_ctrl=False)
        try:
            txt_doc1.update()
            txt_doc2.update()
            txt_ofi.update()
        except Exception:
            pass

        if detectadas > 0:
            show_snackbar(
                page,
                f"Se detectaron {detectadas} ruta(s) de Google Drive automáticamente.",
                tipo="success",
            )
        else:
            show_snackbar(
                page,
                "No se detectaron unidades de Google Drive automáticamente.",
                tipo="warning",
            )

    def _seleccionar_tema(nuevo_tema: str):
        if nuevo_tema == tema_seleccionado[0]:
            return
        tema_seleccionado[0] = nuevo_tema
        valores_actuales = (txt_doc1.value or "", txt_doc2.value or "", txt_ofi.value or "")
        page.close(dlg)
        if on_theme_change:
            on_theme_change(nuevo_tema)
        else:
            settings.guardar_tema(nuevo_tema)
        abrir_config_dialog(
            page,
            file_picker,
            on_saved=on_saved,
            on_theme_change=on_theme_change,
            valores_iniciales=valores_actuales,
        )

    def _crear_opcion_tema(clave: str, titulo: str, subtitulo: str, icono: str, expand_item: bool) -> ft.Container:
        activo = tema_seleccionado[0] == clave
        borde_color = p["primary"] if activo else p["border"]
        fondo = p["primary_soft"] if activo else p["surface_alt"]
        ico_color = p["gold"] if (clave == "dark" and activo) else (p["primary"] if activo else p["text_secondary"])

        return ft.Container(
            expand=expand_item,
            border_radius=12,
            padding=12,
            bgcolor=fondo,
            border=ft.border.all(2 if activo else 1, borde_color),
            ink=True,
            on_click=lambda _, c=clave: _seleccionar_tema(c),
            content=ft.Row(
                [
                    ft.Icon(icono, size=22, color=ico_color),
                    ft.Column(
                        [
                            ft.Text(titulo, size=13, weight=ft.FontWeight.BOLD, color=p["text_primary"]),
                            ft.Text(subtitulo, size=11, color=p["text_secondary"]),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_ROUNDED if activo else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                        size=18,
                        color=p["primary"] if activo else p["text_muted"],
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _guardar(_):
        r_doc1 = (txt_doc1.value or "").strip() or None
        r_doc2 = (txt_doc2.value or "").strip() or None
        r_ofi = (txt_ofi.value or "").strip() or None

        rutas_doc_cambiaron = (
            r_doc1 != settings.ruta_doctorados or r_doc2 != settings.ruta_doctorados2
        )
        ruta_ofi_cambio = r_ofi != settings.ruta_oficios

        settings.guardar_configuracion(r_doc1, r_ofi, r_doc2, current_theme=tema_seleccionado[0])

        if rutas_doc_cambiaron:
            settings.documentos_cargados = False
            settings.documentos_drive = []
            try:
                get_cache().invalidate()
            except Exception:
                pass

        if ruta_ofi_cambio:
            settings.oficios_cargados = False
            settings.documentos_oficios = []
            settings.estructura_oficios = None

        page.close(dlg)
        show_snackbar(page, "Configuración guardada correctamente.", tipo="success")
        if on_saved:
            on_saved()

    en_fila = dlg_w >= 500
    opciones_tema = [
        _crear_opcion_tema(
            "light",
            "Modo Claro",
            "Porcelana y Azul Real UCE",
            ft.Icons.LIGHT_MODE_ROUNDED,
            expand_item=en_fila,
        ),
        _crear_opcion_tema(
            "dark",
            "Modo Oscuro",
            "Obsidiana y Cristal Ahumado",
            ft.Icons.DARK_MODE_ROUNDED,
            expand_item=en_fila,
        ),
    ]
    apariencia_layout: ft.Control = (
        ft.Row(opciones_tema, spacing=12)
        if en_fila
        else ft.Column(opciones_tema, spacing=10)
    )

    icono_header = ft.Container(
        content=ft.Icon(ft.Icons.SETTINGS_ROUNDED, color=p["primary"], size=24),
        padding=8,
        border_radius=10,
        bgcolor=p["primary_soft"],
    )
    col_titulo = ft.Column(
        [
            ft.Text(
                "Configuración General",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=p["text_primary"],
            ),
            ft.Text(
                "Ajusta apariencia y directorios de Google Drive",
                size=12,
                color=p["text_secondary"],
            ),
        ],
        spacing=2,
        expand=True,
    )
    btn_autodetectar = ft.OutlinedButton(
        text="Auto-detectar Drive",
        icon=ft.Icons.AUTO_FIX_HIGH_ROUNDED,
        style=ft.ButtonStyle(
            color=p["primary"],
            side=ft.BorderSide(1, p["primary"]),
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=_autodetectar,
    )
    header_control: ft.Control = (
        ft.Row(
            [icono_header, col_titulo, btn_autodetectar],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        if dlg_w >= 520
        else ft.Column(
            [
                ft.Row(
                    [icono_header, col_titulo],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                btn_autodetectar,
            ],
            spacing=10,
            tight=True,
        )
    )

    body_controls: list[ft.Control] = [
        ft.Text(
            "APARIENCIA",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=p["text_secondary"],
        ),
        apariencia_layout,
        ft.Divider(height=8, color=p["divider"]),
        ft.Text(
            "DIRECTORIOS DE GOOGLE DRIVE",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=p["text_secondary"],
        ),
        _fila_ruta(txt_doc1, ico_doc1, "Seleccionar Directorio de Doctorados UCE"),
        _fila_ruta(txt_doc2, ico_doc2, "Seleccionar Directorio de Doctorados 2"),
        _fila_ruta(txt_ofi, ico_ofi, "Seleccionar Directorio de Oficios"),
    ]
    ideal_h = 375 if en_fila else 455
    max_content_h = max(250, int(vp_h * 0.60))
    if ideal_h > max_content_h:
        content_box = ft.Container(
            width=dlg_w,
            height=max_content_h,
            padding=ft.padding.only(top=6),
            content=ft.Column(
                body_controls,
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
    else:
        content_box = ft.Container(
            width=dlg_w,
            padding=ft.padding.only(top=6),
            content=ft.Column(
                body_controls,
                spacing=12,
                tight=True,
            ),
        )

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=p["surface"],
        shape=ft.RoundedRectangleBorder(radius=16),
        title=header_control,
        content=content_box,
        actions=[
            ft.OutlinedButton(
                text="Cancelar",
                style=ft.ButtonStyle(
                    color=p["danger"],
                    side=ft.BorderSide(1, p["danger"]),
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                on_click=lambda _: page.close(dlg),
            ),
            ft.ElevatedButton(
                text="Guardar Cambios",
                icon=ft.Icons.SAVE_ROUNDED,
                bgcolor=p["success"],
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=_guardar,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    page.open(dlg)
