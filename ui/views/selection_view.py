"""
Vista de selección de módulos
"""
import tkinter as tk
from datetime import datetime
import ui.styles as styles


def mostrar_seleccion(ventana, nombre_usuario, on_docentes, on_oficios, on_acerca_de):
    """
    Muestra pantalla de selección de módulo
    Args:
        ventana: Ventana principal
        nombre_usuario: Nombre del usuario
        on_docentes: Callback para módulo de docentes
        on_oficios: Callback para módulo de oficios
        on_acerca_de: Callback para ver información de la app
    """
    from ui.views.login_view import limpiar_ventana
    limpiar_ventana(ventana)
    
    # Obtener colores del tema activo
    colors = styles.get_theme_colors()
    
    ventana.title("Seleccione una opción")
    ventana.state('zoomed')
    ventana.configure(bg=colors['COLOR_FONDO_MAIN'])

    main_frame = tk.Frame(ventana, bg=colors['COLOR_FONDO_MAIN'])
    main_frame.pack(fill='both', expand=True)

    # Barra superior para botón de ajustes
    top_bar = tk.Frame(main_frame, bg=colors['COLOR_FONDO_MAIN'])
    top_bar.pack(fill='x', side='top', padx=30, pady=(15, 0))

    def abrir_configuracion():
        from ui.views.config_view import ConfigView
        ConfigView(ventana, on_save_callback=lambda: mostrar_seleccion(ventana, nombre_usuario, on_docentes, on_oficios, on_acerca_de))

    btn_settings = tk.Button(
        top_bar,
        text="⚙️ Ajustes",
        command=abrir_configuracion,
        font=("Segoe UI", 11, "bold"),
        bg=colors['COLOR_FONDO_MAIN'],
        fg=colors['COLOR_TEXTO_SECUNDARIO'],
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=15,
        pady=8
    )
    btn_settings.pack(side='right')

    def on_enter_settings(e):
        btn_settings.config(fg=colors['COLOR_ACCENT'], bg=colors['COLOR_ZEBRA_ODD'])
    
    def on_leave_settings(e):
        btn_settings.config(fg=colors['COLOR_TEXTO_SECUNDARIO'], bg=colors['COLOR_FONDO_MAIN'])

    btn_settings.bind("<Enter>", on_enter_settings)
    btn_settings.bind("<Leave>", on_leave_settings)

    # Contenedor de contenido principal centrado
    content = tk.Frame(main_frame, bg=colors['COLOR_FONDO_MAIN'])
    content.place(relx=0.5, rely=0.5, anchor='center')

    # Header
    header = tk.Frame(content, bg=colors['COLOR_FONDO_MAIN'])
    header.pack(pady=(0, 40))

    tk.Label(header, text=f"¡Hola, {nombre_usuario}!", font=("Segoe UI", 32, "bold"),
            bg=colors['COLOR_FONDO_MAIN'], fg=colors['COLOR_TEXTO']).pack(pady=(0, 10))
    
    tk.Label(header, text="Selecciona el módulo que deseas consultar",
            font=("Segoe UI", 16), bg=colors['COLOR_FONDO_MAIN'], fg=colors['COLOR_TEXTO_SECUNDARIO']).pack()

    # Tarjetas
    cards = tk.Frame(content, bg=colors['COLOR_FONDO_MAIN'])
    cards.pack(pady=10)

    # Tarjeta Docentes
    card_doc = tk.Frame(cards, bg=colors['COLOR_FONDO_CARD'], relief="flat", bd=0,
                       highlightthickness=2, highlightbackground=colors['COLOR_BORDER'])
    card_doc.pack(side='left', padx=20, ipadx=40, ipady=30)

    tk.Label(card_doc, text="📚", font=("Segoe UI", 60), bg=colors['COLOR_FONDO_CARD']).pack(pady=(20, 15))
    tk.Label(card_doc, text="DOCENTES", font=("Segoe UI Bold", 22),
            bg=colors['COLOR_FONDO_CARD'], fg=colors['COLOR_TEXTO']).pack(pady=(0, 10))
    tk.Label(card_doc, text="Consulta expedientes\nde doctorados y programas",
            font=("Segoe UI", 12), bg=colors['COLOR_FONDO_CARD'], fg=colors['COLOR_TEXTO_SECUNDARIO'], 
            justify='center').pack(pady=(0, 25))
    
    btn_doc = tk.Button(card_doc, text="ACCEDER →", command=on_docentes,
                       font=("Segoe UI Bold", 14), bg=colors['COLOR_ACCENT'], fg="white",
                       relief="flat", bd=0, padx=40, pady=12, cursor="hand2",
                       activebackground=colors['COLOR_ACCENT_HOVER'], activeforeground="white")
    btn_doc.pack(pady=(0, 20))

    # Tarjeta Oficios
    card_of = tk.Frame(cards, bg=colors['COLOR_FONDO_CARD'], relief="flat", bd=0,
                       highlightthickness=2, highlightbackground=colors['COLOR_BORDER'])
    card_of.pack(side='left', padx=20, ipadx=40, ipady=30)

    tk.Label(card_of, text="📄", font=("Segoe UI", 60), bg=colors['COLOR_FONDO_CARD']).pack(pady=(20, 15))
    tk.Label(card_of, text="OFICIOS", font=("Segoe UI Bold", 22),
            bg=colors['COLOR_FONDO_CARD'], fg=colors['COLOR_TEXTO']).pack(pady=(0, 10))
    tk.Label(card_of, text="Gestiona oficios\ny documentación oficial",
            font=("Segoe UI", 12), bg=colors['COLOR_FONDO_CARD'], fg=colors['COLOR_TEXTO_SECUNDARIO'],
            justify='center').pack(pady=(0, 25))
    
    btn_of = tk.Button(card_of, text="ACCEDER →", command=on_oficios,
                      font=("Segoe UI Bold", 14), bg=colors['COLOR_DANGER'], fg="white",
                      relief="flat", bd=0, padx=40, pady=12, cursor="hand2",
                      activebackground=colors['COLOR_DANGER_HOVER'], activeforeground="white")
    btn_of.pack(pady=(0, 20))

    # Efectos hover
    def on_enter_doc(e):
        card_doc.config(highlightbackground=colors['COLOR_ACCENT'], highlightthickness=3)
        btn_doc.config(bg=colors['COLOR_ACCENT_HOVER'])
    
    def on_leave_doc(e):
        card_doc.config(highlightbackground=colors['COLOR_BORDER'], highlightthickness=2)
        btn_doc.config(bg=colors['COLOR_ACCENT'])

    def on_enter_of(e):
        card_of.config(highlightbackground=colors['COLOR_DANGER'], highlightthickness=3)
        btn_of.config(bg=colors['COLOR_DANGER_HOVER'])
    
    def on_leave_of(e):
        card_of.config(highlightbackground=colors['COLOR_BORDER'], highlightthickness=2)
        btn_of.config(bg=colors['COLOR_DANGER'])

    card_doc.bind("<Enter>", on_enter_doc)
    card_doc.bind("<Leave>", on_leave_doc)
    for w in card_doc.winfo_children():
        w.bind("<Enter>", on_enter_doc)
        w.bind("<Leave>", on_leave_doc)

    card_of.bind("<Enter>", on_enter_of)
    card_of.bind("<Leave>", on_leave_of)
    for w in card_of.winfo_children():
        w.bind("<Enter>", on_enter_of)
        w.bind("<Leave>", on_leave_of)

    # Footer
    footer = tk.Frame(content, bg=colors['COLOR_FONDO_MAIN'])
    footer.pack(pady=(40, 0))

    hora = datetime.now().strftime("%H:%M")
    fecha = datetime.now().strftime("%d de %B, %Y")
    
    tk.Label(footer, text=f"🕐 {hora} • {fecha}", font=("Segoe UI", 11),
            bg=colors['COLOR_FONDO_MAIN'], fg=colors['COLOR_TEXTO_SECUNDARIO']).pack()
    
    # Botón Acerca de
    btn_acerca = tk.Button(
        footer,
        text="ℹ️ Acerca de",
        command=on_acerca_de,
        font=("Segoe UI", 10),
        bg=colors['COLOR_FONDO_MAIN'],
        fg=colors['COLOR_TEXTO_SECUNDARIO'],
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=15,
        pady=8
    )
    btn_acerca.pack(pady=(10, 0))
    
    # Efecto hover
    def on_enter_acerca(e):
        btn_acerca.config(fg=colors['COLOR_ACCENT'], bg=colors['COLOR_ZEBRA_ODD'])
    
    def on_leave_acerca(e):
        btn_acerca.config(fg=colors['COLOR_TEXTO_SECUNDARIO'], bg=colors['COLOR_FONDO_MAIN'])
    
    btn_acerca.bind("<Enter>", on_enter_acerca)
    btn_acerca.bind("<Leave>", on_leave_acerca)
