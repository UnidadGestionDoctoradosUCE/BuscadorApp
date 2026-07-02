"""
Vista de Acerca de - Información de la aplicación
"""
import tkinter as tk
from tkinter import ttk
from ui.views.login_view import limpiar_ventana
from utils.file_utils import resource_path
from PIL import Image, ImageTk


# ==============================================================================
# PALETA PREMIUM
# ==============================================================================
COLOR_FONDO_MAIN = "#FFFFFF"
COLOR_FONDO_SIDEBAR = "#F8F9FA"
COLOR_PRIMARY = "#0EA5E9"
COLOR_PRIMARY_DARK = "#0284C7"
COLOR_ACCENT = "#F97316"
COLOR_TEXTO = "#1E293B"
COLOR_TEXTO_SEC = "#64748B"
COLOR_BORDE = "#E2E8F0"


class AcercaDeView:
    """Vista de Acerca de - Información de la aplicación"""
    
    def __init__(self, ventana, on_volver):
        """Inicializa la vista deAcerca de"""
        self.ventana = ventana
        self.on_volver = on_volver
        
        # Configurar estilos
        self._configurar_estilos()
        
        # Crear interfaz
        self.crear_interfaz()
    
    def _configurar_estilos(self):
        """Configura estilos visuales Premium Flat & Clean"""
        style = ttk.Style(self.ventana)
        style.theme_use('clam')
        
        # Labels
        style.configure("TLabel",
            font=('Segoe UI', 10),
            foreground=COLOR_TEXTO,
            background=COLOR_FONDO_MAIN)
        
        style.configure("Titulo.TLabel",
            font=('Segoe UI', 18, 'bold'),
            foreground=COLOR_TEXTO,
            background=COLOR_FONDO_MAIN)
        
        style.configure("Subtitulo.TLabel",
            font=('Segoe UI', 14, 'bold'),
            foreground=COLOR_PRIMARY,
            background=COLOR_FONDO_MAIN)
        
        style.configure("Info.TLabel",
            font=('Segoe UI', 11),
            foreground=COLOR_TEXTO_SEC,
            background=COLOR_FONDO_MAIN)
        
        style.configure("Nombre.TLabel",
            font=('Segoe UI', 12, 'bold'),
            foreground=COLOR_TEXTO,
            background=COLOR_FONDO_MAIN)
    
    def crear_interfaz(self):
        """Crea toda la interfaz de Acerca de"""
        limpiar_ventana(self.ventana)
        
        # Configurar ventana
        self.ventana.title("Acerca de - Buscador de Documentos")
        self.ventana.state('zoomed')
        self.ventana.configure(bg=COLOR_FONDO_MAIN)
        
        # ==============================================================================
        # CONTENEDOR PRINCIPAL
        # ==============================================================================
        container = tk.Frame(self.ventana, bg=COLOR_FONDO_MAIN)
        container.pack(fill='both', expand=True)
        
        # ==============================================================================
        # SIDEBAR (280px fijo)
        # ==============================================================================
        sidebar = tk.Frame(container, bg=COLOR_FONDO_SIDEBAR, width=280)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # --- Logo ---
        logo_frame = tk.Frame(sidebar, bg=COLOR_FONDO_SIDEBAR)
        logo_frame.pack(pady=30)
        
        try:
            ruta_imagen = resource_path("imagenes/logouce.png")
            imagen_logo = Image.open(ruta_imagen)
            imagen_logo = imagen_logo.resize((80, 80), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(imagen_logo)
            logo_label = tk.Label(logo_frame, image=self.logo_img, bg=COLOR_FONDO_SIDEBAR)
            logo_label.pack()
        except Exception as e:
            print("No se pudo cargar el logo:", e)
        
        # --- Nombre de la app ---
        tk.Label(
            sidebar,
            text="Buscador de\nDocumentos",
            font=('Segoe UI', 14, 'bold'),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO_SIDEBAR,
            justify='center'
        ).pack(pady=(10, 5))
        
        # --- Separator ---
        tk.Frame(sidebar, bg=COLOR_BORDE, height=1).pack(pady=20, padx=30, fill='x')
        
        # --- Botón volver ---
        btn_volver = tk.Button(
            sidebar,
            text="← Volver",
            font=('Segoe UI', 11, 'bold'),
            bg="#0369A1",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.on_volver
        )
        btn_volver.pack(pady=20, padx=30, fill='x')
        
        # ==============================================================================
        # MAIN CONTENT (derecha)
        # ==============================================================================
        main = tk.Frame(container, bg=COLOR_FONDO_MAIN)
        main.pack(side='left', fill='both', expand=True, padx=40, pady=30)
        
        # --- Título principal ---
        tk.Label(
            main,
            text="Acerca de la Aplicación",
            font=('Segoe UI', 24, 'bold'),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO_MAIN
        ).pack(pady=(10, 20))
        
        # --- Card de información (Contenedor de 2 columnas) ---
        card = tk.Frame(
            main, 
            bg=COLOR_FONDO_MAIN, 
            highlightbackground=COLOR_BORDE, 
            highlightcolor=COLOR_BORDE,
            highlightthickness=1,
            bd=0
        )
        card.pack(fill='both', expand=True, pady=(0, 20))
        
        # --- Columna Izquierda: Detalles Técnicos ---
        col_izquierda = tk.Frame(card, bg=COLOR_FONDO_MAIN)
        col_izquierda.pack(side='left', fill='both', expand=True, padx=25, pady=25)
        
        tk.Label(
            col_izquierda,
            text="Detalles Técnicos",
            font=('Segoe UI', 12, 'bold'),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO_MAIN
        ).pack(pady=(0, 15), anchor='w')
        
        # Versión
        self._crear_info_row(col_izquierda, "Versión", "1.0.0")
        
        # Separator
        tk.Frame(col_izquierda, bg=COLOR_BORDE, height=1).pack(pady=10, fill='x')
        
        # Lenguaje
        self._crear_info_row(col_izquierda, "Lenguaje de Programación", "Python 3.14")
        
        # Separator
        tk.Frame(col_izquierda, bg=COLOR_BORDE, height=1).pack(pady=10, fill='x')
        
        # Interfaz Gráfica
        self._crear_info_row(col_izquierda, "Interfaz Gráfica", "Tkinter")
        
        # --- Separador Vertical ---
        separador_v = tk.Frame(card, bg=COLOR_BORDE, width=1)
        separador_v.pack(side='left', fill='y', pady=20)
        
        # --- Columna Derecha: Equipo y Universidad ---
        col_derecha = tk.Frame(card, bg=COLOR_FONDO_MAIN)
        col_derecha.pack(side='left', fill='both', expand=True, padx=25, pady=25)
        
        tk.Label(
            col_derecha,
            text="Equipo y Universidad",
            font=('Segoe UI', 12, 'bold'),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO_MAIN
        ).pack(pady=(0, 15), anchor='w')
        
        # Universidad
        self._crear_info_row(col_derecha, "Universidad", "Universidad Central del Ecuador")
        
        # Separator
        tk.Frame(col_derecha, bg=COLOR_BORDE, height=1).pack(pady=10, fill='x')
        
        # Carrera
        self._crear_info_row(col_derecha, "Carrera", "Ingeniería en Ciencias de la Computación")
        
        # Separator
        tk.Frame(col_derecha, bg=COLOR_BORDE, height=1).pack(pady=10, fill='x')
        
        # Desarrolladores
        tk.Label(
            col_derecha,
            text="Desarrolladores",
            font=('Segoe UI', 10, 'bold'),
            fg=COLOR_TEXTO_SEC,
            bg=COLOR_FONDO_MAIN
        ).pack(pady=(2, 4), anchor='w')
        
        devs_frame = tk.Frame(col_derecha, bg=COLOR_FONDO_MAIN)
        devs_frame.pack(anchor='w', fill='x')
        
        desarrolladores = [
            "Bryan Loya",
            "Wulfer Quiguango",
            "Marielena Gonzalez",
            "Mariel Milan"
        ]
        
        for dev in desarrolladores:
            tk.Label(
                devs_frame,
                text=f"• {dev}",
                font=('Segoe UI', 11),
                fg=COLOR_PRIMARY,
                bg=COLOR_FONDO_MAIN
            ).pack(pady=1, anchor='w')
        
        # --- Pie de página ---
        tk.Label(
            main,
            text="© 2024 - Todos los derechos reservados",
            font=('Segoe UI', 9),
            fg=COLOR_TEXTO_SEC,
            bg=COLOR_FONDO_MAIN
        ).pack(pady=10)
    
    def _crear_info_row(self, parent, label, valor, row=None):
        """Crea una fila de información label: valor"""
        tk.Label(
            parent,
            text=label,
            font=('Segoe UI', 10, 'bold'),
            fg=COLOR_TEXTO_SEC,
            bg=COLOR_FONDO_MAIN
        ).pack(pady=(2, 1), anchor='w')
        
        tk.Label(
            parent,
            text=valor,
            font=('Segoe UI', 11),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO_MAIN
        ).pack(pady=(1, 2), anchor='w')
    
    def refrescar_vista(self):
        """Recrea la interfaz"""
        self.crear_interfaz()


def mostrar_acerca_de(ventana, on_volver):
    """Función helper para mostrar la vista deAcerca de"""
    AcercaDeView(ventana, on_volver)
