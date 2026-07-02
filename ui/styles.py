"""
Configuración de estilos y temas de la interfaz de usuario
"""
from tkinter import ttk


"""
Configuración de estilos y temas de la interfaz de usuario
"""
import tkinter as tk
from tkinter import ttk
import config.settings as settings

# Paleta de colores original limpia y clara
THEMES = {
    "light": {
        "COLOR_FONDO_MAIN": "#F5F7FA",       # Gris claro muy suave
        "COLOR_FONDO_CARD": "#FFFFFF",       # Blanco puro para tarjetas
        "COLOR_TEXTO": "#2C3E50",            # Gris azulado oscuro
        "COLOR_TEXTO_SECUNDARIO": "#6C757D", # Gris medio para detalles
        "COLOR_ACCENT": "#3498DB",           # Azul brillante
        "COLOR_ACCENT_HOVER": "#2980B9",     # Azul hover
        "COLOR_ZEBRA_EVEN": "#FFFFFF",       # Blanco para celdas pares
        "COLOR_ZEBRA_ODD": "#F1F5F9",        # Gris muy claro para celdas impares
        "COLOR_SUCCESS": "#2ECC71",          # Verde esmeralda
        "COLOR_SUCCESS_HOVER": "#27AE60",    # Verde hover
        "COLOR_DANGER": "#E74C3C",           # Rojo coral
        "COLOR_DANGER_HOVER": "#C0392B",     # Rojo hover
        "COLOR_BORDER": "#E2E8F0"            # Borde claro
    }
}


def get_theme_colors():
    """
    Retorna la paleta de colores original limpia y clara.
    """
    return THEMES["light"]


def actualizar_widgets_recursivo(widget, colors):
    """
    Recorre recursivamente la jerarquía de widgets y actualiza sus colores
    de acuerdo al tema activo para widgets estándar de Tkinter.
    """
    try:
        # Ignorar si es un widget ttk de forma explícita para evitar romper estilos de la suite ttk
        widget_class = widget.winfo_class()
        
        # Evaluar widgets de Tkinter estándar
        if isinstance(widget, tk.Frame) and not isinstance(widget, ttk.Frame):
            widget.config(bg=colors['COLOR_FONDO_MAIN'])
            
        elif isinstance(widget, tk.Label) and not isinstance(widget, ttk.Label):
            # Si el Label está en un contenedor, puede heredar su fondo o usar COLOR_FONDO_MAIN
            bg_parent = colors['COLOR_FONDO_MAIN']
            if hasattr(widget.master, 'cget'):
                try:
                    bg_parent = widget.master.cget('bg')
                except:
                    pass
            # Para evitar que etiquetas con colores especiales sean modificadas a la fuerza
            widget.config(bg=bg_parent, fg=colors['COLOR_TEXTO'])
            
        elif isinstance(widget, tk.Entry) and not isinstance(widget, ttk.Entry):
            widget.config(bg=colors['COLOR_ZEBRA_ODD'], fg=colors['COLOR_TEXTO'], 
                          insertbackground=colors['COLOR_TEXTO'], selectbackground=colors['COLOR_ACCENT'],
                          highlightcolor=colors['COLOR_ACCENT'], highlightbackground=colors['COLOR_BORDER'])
            
        elif isinstance(widget, tk.Button) and not isinstance(widget, ttk.Button):
            widget.config(bg=colors['COLOR_ACCENT'], fg="white", 
                          activebackground=colors['COLOR_ACCENT_HOVER'], activeforeground="white")
            
        elif isinstance(widget, tk.Text):
            widget.config(bg=colors['COLOR_ZEBRA_ODD'], fg=colors['COLOR_TEXTO'], 
                          insertbackground=colors['COLOR_TEXTO'])
            
        elif isinstance(widget, tk.Canvas):
            widget.config(bg=colors['COLOR_FONDO_MAIN'], highlightthickness=0)
            
        elif isinstance(widget, tk.LabelFrame) and not isinstance(widget, ttk.LabelFrame):
            widget.config(bg=colors['COLOR_FONDO_MAIN'], fg=colors['COLOR_TEXTO'])
            
        elif isinstance(widget, tk.Checkbutton) and not isinstance(widget, ttk.Checkbutton):
            widget.config(bg=colors['COLOR_FONDO_MAIN'], fg=colors['COLOR_TEXTO'], 
                          activebackground=colors['COLOR_FONDO_MAIN'], selectcolor=colors['COLOR_ZEBRA_ODD'])
            
        elif isinstance(widget, tk.Radiobutton) and not isinstance(widget, ttk.Radiobutton):
            widget.config(bg=colors['COLOR_FONDO_MAIN'], fg=colors['COLOR_TEXTO'], 
                          activebackground=colors['COLOR_FONDO_MAIN'], selectcolor=colors['COLOR_ZEBRA_ODD'])
            
    except Exception as e:
        print(f"[WARN] Error actualizando widget {widget}: {e}")

    # Procesar hijos
    for child in widget.winfo_children():
        actualizar_widgets_recursivo(child, colors)


def configurar_estilos(root=None):
    """
    Configura todos los estilos ttk de la aplicación
    """
    colors = get_theme_colors()
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configurar componentes básicos de ttk
    style.configure('TFrame', background=colors['COLOR_FONDO_MAIN'])
    style.configure('TLabel', background=colors['COLOR_FONDO_MAIN'], foreground=colors['COLOR_TEXTO'])
    style.configure('TLabelframe', background=colors['COLOR_FONDO_MAIN'], foreground=colors['COLOR_TEXTO'])
    style.configure('TLabelframe.Label', background=colors['COLOR_FONDO_MAIN'], foreground=colors['COLOR_TEXTO'])
    
    # Treeview moderno con mejor diseño
    style.configure("Treeview",
                    background=colors['COLOR_ZEBRA_EVEN'],
                    foreground=colors['COLOR_TEXTO'],
                    rowheight=32,
                    fieldbackground=colors['COLOR_ZEBRA_EVEN'],
                    font=('Segoe UI', 9),
                    borderwidth=0,
                    relief='flat')
    
    style.configure("Treeview.Heading",
                    background=colors['COLOR_BORDER'],
                    foreground=colors['COLOR_TEXTO'],
                    font=('Segoe UI', 9, 'bold'),
                    borderwidth=0,
                    relief='flat')
    
    style.map('Treeview.Heading',
              background=[('active', colors['COLOR_ZEBRA_ODD'])])
    
    style.map('Treeview', 
              background=[('selected', colors['COLOR_ACCENT'])], 
              foreground=[('selected', 'white')])
    
    try:
        # Scrollbar moderna
        style.configure("Vertical.TScrollbar",
                        gripcount=0,
                        background=colors['COLOR_BORDER'],
                        troughcolor=colors['COLOR_FONDO_MAIN'],
                        bordercolor=colors['COLOR_FONDO_MAIN'],
                        darkcolor=colors['COLOR_FONDO_MAIN'],
                        lightcolor=colors['COLOR_FONDO_MAIN'],
                        arrowsize=0,
                        width=10)

        style.map("Vertical.TScrollbar",
                  background=[('active', colors['COLOR_ACCENT']), ('!active', colors['COLOR_BORDER'])])
    except Exception as e:
        print(f"[WARN] Error configurando scrollbar custom: {e}")
    
    # Botones principales con diseño moderno
    style.configure('TButton', 
                    font=('Segoe UI', 11, 'bold'), 
                    padding=10,
                    relief='flat',
                    background=colors['COLOR_ACCENT'],
                    foreground='white',
                    borderwidth=0)
    
    style.map('TButton',
              background=[('active', colors['COLOR_ACCENT_HOVER']), ('pressed', colors['COLOR_ACCENT_HOVER'])],
              foreground=[('active', 'white'), ('pressed', 'white')])
    
    # Combobox mejorado
    style.configure('TCombobox', 
                    font=('Segoe UI', 10),
                    fieldbackground=colors['COLOR_ZEBRA_EVEN'],
                    background=colors['COLOR_ZEBRA_EVEN'],
                    selectbackground=colors['COLOR_ACCENT'],
                    selectforeground='white',
                    borderwidth=1,
                    relief='solid')
    
    style.map('TCombobox',
              fieldbackground=[('readonly', colors['COLOR_ZEBRA_EVEN'])],
              selectbackground=[('readonly', colors['COLOR_ACCENT'])],
              selectforeground=[('readonly', 'white')])
    
    # Botón Cerrar Sesión moderno
    style.configure('CerrarSesion.TButton', 
                    font=('Segoe UI', 10, 'bold'), 
                    padding=10,
                    background=colors['COLOR_DANGER'],
                    foreground='white',
                    relief='flat',
                    borderwidth=0)
    
    style.map('CerrarSesion.TButton',
              background=[('active', colors['COLOR_DANGER_HOVER']), ('pressed', colors['COLOR_DANGER_HOVER'])],
              foreground=[('active', 'white'), ('pressed', 'white')])
    
    # Botón Sincronizar moderno
    style.configure('Sincronizar.TButton', 
                    font=('Segoe UI', 10, 'bold'), 
                    padding=10,
                    background=colors['COLOR_SUCCESS'],
                    foreground='white',
                    relief='flat',
                    borderwidth=0)
    
    style.map('Sincronizar.TButton',
              background=[('active', colors['COLOR_SUCCESS_HOVER']), ('pressed', colors['COLOR_SUCCESS_HOVER'])],
              foreground=[('active', 'white'), ('pressed', 'white')])
    
    # Botón de Login
    style.configure('Login.TButton', 
                    font=('Segoe UI', 13, 'bold'), 
                    padding=12,
                    background=colors['COLOR_ACCENT'],
                    foreground='white',
                    relief='flat',
                    borderwidth=0)
    
    style.map('Login.TButton',
              background=[('active', colors['COLOR_ACCENT_HOVER']), ('pressed', colors['COLOR_ACCENT_HOVER'])])

    # Si se pasa un root widget, aplicar recursivamente para repintar
    if root:
        actualizar_widgets_recursivo(root, colors)

