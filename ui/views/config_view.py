"""
Vista de Configuración - Permite configurar las rutas de Google Drive y el Tema (Claro/Oscuro)
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import config.settings as settings
import ui.styles as styles


class ConfigView(tk.Toplevel):
    """Ventana modal premium para la configuración del sistema"""
    
    def __init__(self, master, on_save_callback=None):
        """
        Inicializa la ventana de configuración
        Args:
            master: Ventana padre (Tk or Toplevel)
            on_save_callback: Callback opcional a ejecutar al guardar la configuración
        """
        super().__init__(master)
        self.master = master
        self.on_save_callback = on_save_callback
        
        # Hacer la ventana modal
        self.transient(master)
        self.grab_set()
        
        # Configurar propiedades de la ventana
        self.title("Configuración de Sistema ⚙️")
        self.geometry("620x420")
        self.resizable(False, False)
        
        # Centrar la ventana respecto al padre
        self.center_window()
        
        # Cargar colores actuales del tema
        self.colors = styles.get_theme_colors()
        self.configure(bg=self.colors['COLOR_FONDO_MAIN'])
        
        # Variables de control
        self.var_doc1 = tk.StringVar(value=settings.ruta_doctorados or "")
        self.var_doc2 = tk.StringVar(value=settings.ruta_doctorados2 or "")
        self.var_ofi = tk.StringVar(value=settings.ruta_oficios or "")
        
        # Crear la interfaz
        self.crear_interfaz()
        
    def center_window(self):
        """Centra la ventana en la pantalla o sobre el padre"""
        self.update_idletasks()
        width = 620
        height = 420
        
        # Obtener coordenadas del padre
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        
        # Calcular posición centrada
        x = master_x + (master_width - width) // 2
        y = master_y + (master_height - height) // 2
        
        # Limitar para que no salga de la pantalla
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        
        self.geometry(f"{width}x{height}+{x}+{y}")

    def crear_interfaz(self):
        """Dibuja todos los widgets con un diseño premium y pulido"""
        # Limpiar widgets previos (útil si refrescamos tema)
        for child in self.winfo_children():
            child.destroy()
            
        # Contenedor principal acolchado
        self.main_frame = tk.Frame(self, bg=self.colors['COLOR_FONDO_MAIN'], padx=25, pady=25)
        self.main_frame.pack(fill='both', expand=True)
        
        # Título principal
        titulo = tk.Label(
            self.main_frame,
            text="Configuración General",
            font=('Segoe UI', 18, 'bold'),
            fg=self.colors['COLOR_TEXTO'],
            bg=self.colors['COLOR_FONDO_MAIN']
        )
        titulo.pack(anchor='w', pady=(0, 5))
        
        subtitulo = tk.Label(
            self.main_frame,
            text="Ajuste las rutas de base de datos de Google Drive.",
            font=('Segoe UI', 10),
            fg=self.colors['COLOR_TEXTO_SECUNDARIO'],
            bg=self.colors['COLOR_FONDO_MAIN']
        )
        subtitulo.pack(anchor='w', pady=(0, 25))
        
        # ----------------------------------------------------------------------
        # SECCIÓN 1: RUTAS DE GOOGLE DRIVE (Tarjeta)
        # ----------------------------------------------------------------------
        seccion_rutas = tk.LabelFrame(
            self.main_frame,
            text=" Directorios de Google Drive ",
            font=('Segoe UI', 11, 'bold'),
            fg=self.colors['COLOR_TEXTO'],
            bg=self.colors['COLOR_FONDO_MAIN'],
            bd=1,
            relief='solid',
            padx=15,
            pady=15
        )
        seccion_rutas.pack(fill='x', pady=(0, 20))
        
        # Fila 1: Ruta Doctorados 1
        lbl_doc1 = tk.Label(
            seccion_rutas,
            text="Ruta Doctorados UCE (DB General):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['COLOR_TEXTO_SECUNDARIO'],
            bg=self.colors['COLOR_FONDO_MAIN']
        )
        lbl_doc1.pack(anchor='w')
        
        frame_doc1 = tk.Frame(seccion_rutas, bg=self.colors['COLOR_FONDO_MAIN'])
        frame_doc1.pack(fill='x', pady=(2, 10))
        
        entry_doc1 = tk.Entry(
            frame_doc1,
            textvariable=self.var_doc1,
            font=('Segoe UI', 10),
            bg=self.colors['COLOR_ZEBRA_ODD'],
            fg=self.colors['COLOR_TEXTO'],
            insertbackground=self.colors['COLOR_TEXTO'],
            bd=1,
            relief='solid'
        )
        entry_doc1.pack(side='left', fill='x', expand=True, ipady=4, padx=(0, 8))
        
        btn_browse_doc1 = tk.Button(
            frame_doc1,
            text="Examinar 📂",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['COLOR_ACCENT'],
            fg="white",
            activebackground=self.colors['COLOR_ACCENT_HOVER'],
            activeforeground="white",
            relief='flat',
            bd=0,
            cursor="hand2",
            padx=10,
            command=self.buscar_ruta_doc1
        )
        btn_browse_doc1.pack(side='right')

        # Fila 2: Ruta Doctorados 2
        lbl_doc2 = tk.Label(
            seccion_rutas,
            text="Ruta Doctorados 2 (DB General 2):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['COLOR_TEXTO_SECUNDARIO'],
            bg=self.colors['COLOR_FONDO_MAIN']
        )
        lbl_doc2.pack(anchor='w')
        
        frame_doc2 = tk.Frame(seccion_rutas, bg=self.colors['COLOR_FONDO_MAIN'])
        frame_doc2.pack(fill='x', pady=(2, 10))
        
        entry_doc2 = tk.Entry(
            frame_doc2,
            textvariable=self.var_doc2,
            font=('Segoe UI', 10),
            bg=self.colors['COLOR_ZEBRA_ODD'],
            fg=self.colors['COLOR_TEXTO'],
            insertbackground=self.colors['COLOR_TEXTO'],
            bd=1,
            relief='solid'
        )
        entry_doc2.pack(side='left', fill='x', expand=True, ipady=4, padx=(0, 8))
        
        btn_browse_doc2 = tk.Button(
            frame_doc2,
            text="Examinar 📂",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['COLOR_ACCENT'],
            fg="white",
            activebackground=self.colors['COLOR_ACCENT_HOVER'],
            activeforeground="white",
            relief='flat',
            bd=0,
            cursor="hand2",
            padx=10,
            command=self.buscar_ruta_doc2
        )
        btn_browse_doc2.pack(side='right')

        # Fila 3: Ruta Oficios
        lbl_ofi = tk.Label(
            seccion_rutas,
            text="Ruta Oficios (DB General Oficios):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['COLOR_TEXTO_SECUNDARIO'],
            bg=self.colors['COLOR_FONDO_MAIN']
        )
        lbl_ofi.pack(anchor='w')
        
        frame_ofi = tk.Frame(seccion_rutas, bg=self.colors['COLOR_FONDO_MAIN'])
        frame_ofi.pack(fill='x', pady=(2, 2))
        
        entry_ofi = tk.Entry(
            frame_ofi,
            textvariable=self.var_ofi,
            font=('Segoe UI', 10),
            bg=self.colors['COLOR_ZEBRA_ODD'],
            fg=self.colors['COLOR_TEXTO'],
            insertbackground=self.colors['COLOR_TEXTO'],
            bd=1,
            relief='solid'
        )
        entry_ofi.pack(side='left', fill='x', expand=True, ipady=4, padx=(0, 8))
        
        btn_browse_ofi = tk.Button(
            frame_ofi,
            text="Examinar 📂",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['COLOR_ACCENT'],
            fg="white",
            activebackground=self.colors['COLOR_ACCENT_HOVER'],
            activeforeground="white",
            relief='flat',
            bd=0,
            cursor="hand2",
            padx=10,
            command=self.buscar_ruta_ofi
        )
        btn_browse_ofi.pack(side='right')

        # ----------------------------------------------------------------------
        # BOTONES DE ACCIÓN (Guardar / Cancelar)
        # ----------------------------------------------------------------------
        frame_acciones = tk.Frame(self.main_frame, bg=self.colors['COLOR_FONDO_MAIN'])
        frame_acciones.pack(fill='x', side='bottom', pady=(10, 0))
        
        btn_cancelar = tk.Button(
            frame_acciones,
            text="Cancelar",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['COLOR_DANGER'],
            fg="white",
            activebackground=self.colors['COLOR_DANGER_HOVER'],
            activeforeground="white",
            relief='flat',
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8,
            command=self.cancelar
        )
        btn_cancelar.pack(side='left')
        
        btn_guardar = tk.Button(
            frame_acciones,
            text="Guardar Cambios 💾",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['COLOR_SUCCESS'],
            fg="white",
            activebackground=self.colors['COLOR_SUCCESS_HOVER'],
            activeforeground="white",
            relief='flat',
            bd=0,
            cursor="hand2",
            padx=25,
            pady=8,
            command=self.guardar_cambios
        )
        btn_guardar.pack(side='right')

    def buscar_ruta_doc1(self):
        """Abre buscador para Doctorados 1"""
        dir_seleccionado = filedialog.askdirectory(
            title="Seleccionar Directorio de Doctorados UCE (General)",
            initialdir=self.var_doc1.get() or "/"
        )
        if dir_seleccionado:
            self.var_doc1.set(os.path.normpath(dir_seleccionado))
            
    def buscar_ruta_doc2(self):
        """Abre buscador para Doctorados 2"""
        dir_seleccionado = filedialog.askdirectory(
            title="Seleccionar Directorio de Doctorados 2",
            initialdir=self.var_doc2.get() or "/"
        )
        if dir_seleccionado:
            self.var_doc2.set(os.path.normpath(dir_seleccionado))

    def buscar_ruta_ofi(self):
        """Abre buscador para Oficios"""
        dir_seleccionado = filedialog.askdirectory(
            title="Seleccionar Directorio de Oficios (GeneralOficios)",
            initialdir=self.var_ofi.get() or "/"
        )
        if dir_seleccionado:
            self.var_ofi.set(os.path.normpath(dir_seleccionado))

    def guardar_cambios(self):
        """Valida y persiste los cambios de configuración y aplica el tema"""
        r_doc1 = self.var_doc1.get().strip() or None
        r_doc2 = self.var_doc2.get().strip() or None
        r_ofi = self.var_ofi.get().strip() or None
        
        # Validar que al menos una ruta de Drive esté configurada
        if not r_doc1 and not r_ofi:
            messagebox.showwarning(
                "Advertencia de Configuración",
                "Hermano, tenés que configurar al menos la ruta de Doctorados 1 o la de Oficios para poder buscar algo.",
                parent=self
            )
        
        # Guardar en settings.json
        settings.guardar_configuracion(r_doc1, r_ofi, r_doc2)
        
        # Ejecutar callback si existe
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception as e:
                print(f"[WARN] Error en callback de guardado: {e}")
                
        # Mostrar mensaje de éxito
        messagebox.showinfo(
            "Configuración Guardada",
            "¡Espectacular! La configuración se guardó correctamente. ¡De una!",
            parent=self.master
        )
        
        self.destroy()
        
    def cancelar(self):
        """Cancela y cierra"""
        self.destroy()
