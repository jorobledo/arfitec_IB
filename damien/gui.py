from cProfile import label
import tkinter as tk
import numpy as np
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import Menu
from pathlib import Path
import re

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import os

from physics import process_neutron_data

from plot import (
    plot_1,
    plot_2,
    plot_3,
    plot_4,
    plot_5,
    plot_6,
    plot_7,
    plot_8,
    plot_9,
    plot_10,
    plot_11,
    plot_12,
    plot_flux_tof,
    plot_flux_energy
)

# Import correction (removal of .py)
from utils import (
    grouped_file
)

from config import PARAMS


# ==========================================================
# GUI APPLICATION
# ==========================================================

class NeutronApp:

    # ======================================================
    # INIT
    # ======================================================

    def __init__(self, root):
        
        # --- STATE FLAGS ---
        self.is_loading = False  # Blocks user inputs during heavy I/O operations
        self.apply_y_limits = False

        self.root = root
        self.root.title("Neutron Spectrum Analysis (Chopper Experiment)")
        self.root.state("zoomed")
        
        # --- MENU BAR CREATION ---
        barre_menu = Menu(self.root)
        self.root.config(menu=barre_menu)

        # 1. "File" Dropdown Menu
        menu_fichier = Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label="File", menu=menu_fichier)
        menu_fichier.add_command(label="Save Plot", command=self.save_current_plot)
        menu_fichier.add_command(label="Export Data", command=self.export_current_data)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Exit", command=self.root.quit)

        # 2. "Tools" Dropdown Menu
        menu_outils = Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label="Tools", menu=menu_outils)
        menu_outils.add_command(label="Group Files", command=self.action_grouper_fichiers)

        # 3. "Help" Dropdown Menu
        menu_help = Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label="Help", menu=menu_help)
        menu_help.add_command(label="User Guide", command=self.show_user_guide)
        menu_help.add_command(label="Recommended Workflow",command=self.show_workflow)
        menu_help.add_command(label="Plot Reference",command=self.show_plot_reference)
        menu_help.add_separator()
        menu_help.add_command(label="About",command=self.show_about)
        

        # ==================================================
        # DESIGN & STYLES (TABS & FONTS)
        # ==================================================
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Colors of our modern design system
        BG_DARK = "#2c3e50"      # Dark slate blue for left panel
        TEXT_LIGHT = "#d3d3d3"   # Light gray for left panel text
        FONT_MAIN = ("Segoe UI", 10)
        FONT_BOLD = ("Segoe UI", 11, "bold")
        
        # Tab configuration
        self.style.configure("TNotebook.Tab", background="#95a5a6", foreground="black", padding=[18, 6], font=("Segoe UI", 10))
        self.style.map("TNotebook.Tab", background=[("selected", "#34495e")], foreground=[("selected", "#d3d3d3")], font=[("selected", ("Segoe UI", 10, "bold"))])

        # DATA STORAGE & CACHE
        # --------------------------------------------------
        self.datasets = {}
        self.fit_results = None
        self.plot_history = []  # Plot history for replay
        self.is_replaying = False

        # ==================================================
        # MAIN LAYOUT WITH NOTEBOOK (TABS)
        # ==================================================
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_analysis = tk.Frame(self.notebook)
        self.tab_config = tk.Frame(self.notebook)
        self.tab_stats = tk.Frame(self.notebook)

        self.notebook.add(self.tab_analysis, text=" Analysis & Control ")
        self.notebook.add(self.tab_config, text=" Physical Parameters ")
        self.notebook.add(self.tab_stats, text=" Fit Results & Stats ")
        
        # --- STATUS BAR --- (Fixed here with tk.Label)
        self.status_label = tk.Label(self.root, text="Ready", bd=1, relief="sunken", anchor="w")
        self.status_label.pack(side="bottom", fill="x")

        # ==================================================
        # TAB 1: ANALYSIS & CONTROL LAYOUT
        # ==================================================
        self.tab_analysis.grid_columnconfigure(0, weight=0) 
        self.tab_analysis.grid_columnconfigure(1, weight=1) 
        self.tab_analysis.grid_rowconfigure(0, weight=1)

        # 1. Left control panel (Dark Style & High Contrast)
        self.control_frame = tk.Frame(
            self.tab_analysis,
            width=280,
            bg=BG_DARK
        )
        self.control_frame.pack_propagate(False)
        self.control_frame.grid(row=0, column=0, sticky="nsw")

        # 2. Right graphical area
        self.plot_frame_container = tk.Frame(self.tab_analysis, bg="#ffffff")
        self.plot_frame_container.grid(row=0, column=1, sticky="nsew")
        
        # Split the right area to integrate history bar at the top
        self.plot_frame_container.grid_rowconfigure(0, weight=0) # Top bar (History)
        self.plot_frame_container.grid_rowconfigure(1, weight=1) # Graph
        self.plot_frame_container.grid_columnconfigure(0, weight=1)

        # TOP RIGHT BAR: History dropdown menu
        self.top_bar = tk.Frame(self.plot_frame_container, bg="#f8f9fa", height=40, bd=1, relief=tk.RIDGE)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.history_label = tk.Label(self.top_bar, text="Plot History :", bg="#f8f9fa", font=("Segoe UI", 10, "bold"), fg="#333333")
        self.history_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.history_combobox = ttk.Combobox(self.top_bar, state="readonly", width=45, font=("Segoe UI", 9))
        self.history_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.history_combobox.set("No history yet")
        self.history_combobox.bind("<<ComboboxSelected>>", self.replay_plot_from_history)

        # Actual area where matplotlib will draw
        self.plot_frame = tk.Frame(self.plot_frame_container, bg="#ffffff")
        self.plot_frame.grid(row=1, column=0, sticky="nsew")

        # ==================================================
        # LEFT PANEL: TITLE
        # ==================================================
        self.title_label = tk.Label(
            self.control_frame,
            text="NEUTRON ANALYSIS",
            font=("Segoe UI", 14, "bold"),
            bg=BG_DARK,
            fg="#f1c40f" # Bright yellow for perfect contrast
        )
        self.title_label.pack(pady=(25, 15))

        # LEFT PANEL: LOAD BUTTONS
        # ==================================================
        self.load_button = tk.Button(
            self.control_frame,
            text="Load Data Files",
            command=self.load_files,
            font=FONT_MAIN,
            bg="#34495e",
            fg=TEXT_LIGHT,
            activebackground="#5d6d7e",
            activeforeground=TEXT_LIGHT,
            bd=0, height=1, width=22, cursor="hand2"
        )
        self.load_button.pack(pady=5)

        self.clear_cache_button = tk.Button(
            self.control_frame,
            text="Clear Cache / Reset",
            command=self.clear_cache,
            font=("Segoe UI", 9),
            bg="#7f8c8d",
            fg=TEXT_LIGHT,
            activebackground="#95a5a6",
            activeforeground=TEXT_LIGHT,
            bd=0, height=1, width=22, cursor="hand2"
        )
        self.clear_cache_button.pack(pady=(2, 5))

        # LEFT PANEL: FILE LIST
        # ==================================================
        self.file_label = tk.Label(
            self.control_frame,
            text="Loaded Files",
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            font=FONT_BOLD
        )
        self.file_label.pack(pady=(5, 2))

        self.file_listbox = tk.Listbox(
            self.control_frame,
            width=32,
            height=8,
            selectmode=tk.EXTENDED,
            exportselection=False,
            bg="#34495e",
            fg=TEXT_LIGHT,
            selectbackground="#1abc9c", # Emerald green for selection
            selectforeground=TEXT_LIGHT,
            font=("Consolas", 9),
            bd=0, highlightthickness=1, highlightbackground="#455a64"
        )
        self.file_listbox.pack(padx=15, pady=5)
        
        self.ordre_selection = []
        self.file_listbox.bind('<<ListboxSelect>>', self.maj_ordre_selection)

        # ==================================================
        # LEFT PANEL : QUICK FLUX PLOTS
        # ==================================================

        self.flux_frame = tk.LabelFrame(
            self.control_frame,
            text="Flux",
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            font=FONT_BOLD,
            padx=10,
            pady=6
        )
        

        self.flux_frame.pack(
            padx=12,
            pady=(2,1)
        )

        self.tof_flux_button = tk.Button(
            self.flux_frame,
            text="ToF Flux",
            command=self.execute_flux_tof,
            width=14,
            bg="#566573",
            fg=TEXT_LIGHT,
            activebackground="#707b7c",
            bd=0,
            cursor="hand2"
        )
        self.tof_flux_button.pack(side=tk.LEFT, padx=6)

        self.energy_flux_button = tk.Button(
            self.flux_frame,
            text="Energy Flux",
            command=self.execute_flux_energy,
            width=14,
            bg="#566573",
            fg=TEXT_LIGHT,
            activebackground="#707b7c",
            bd=0,
            cursor="hand2"
        )
        self.energy_flux_button.pack(side=tk.RIGHT, padx=6)


        # ==================================================
        # LEFT PANEL : ANALYSIS MENU
        # ==================================================

        self.analysis_frame = tk.LabelFrame(
            self.control_frame,
            text="Analysis",
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            font=FONT_BOLD,
            padx=14,
            pady=6
        )

        self.analysis_frame.pack(
            padx=12,
            pady=(1,1)
        )

        # Current selected analysis
        self.selected_analysis_id = "1"

        self.selected_plot_label = tk.StringVar()
        self.selected_plot_label.set("Select Analysis")

        self.select_plot_button = tk.Button(
            self.analysis_frame,
            textvariable=self.selected_plot_label,
            command=self.show_analysis_menu,
            width=24,
            bg="#496682",
            fg=TEXT_LIGHT,
            bd=0,
            cursor="hand2"
        )
        self.select_plot_button.pack(side=tk.LEFT)

        self.ok_button = tk.Button(
            self.analysis_frame,
            text="OK",
            command=self.execute_analysis_plot,
            width=5,
            bg="#7897b9",
            fg=TEXT_LIGHT,
            bd=0,
            cursor="hand2"
        )
        self.ok_button.pack(side=tk.RIGHT, padx=6)


        # ==================================================
        # LEFT PANEL : FIT BUTTON
        # ==================================================

        self.fit_frame = tk.LabelFrame(
            self.control_frame,
            text="Fit",
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            font=FONT_BOLD,
            padx=14,
            pady=6
        )

        self.fit_frame.pack(
            padx=12,
            pady=(1,8)
        )

        # Current selected fit
        self.selected_fit_id = "6"

        self.selected_fit_label = tk.StringVar()
        self.selected_fit_label.set("Select Fit")

        self.fit_button = tk.Button(
            self.fit_frame ,
            textvariable=self.selected_fit_label,
            command=self.show_fit_menu,
            width=24,
            bg="#496682",
            fg=TEXT_LIGHT,
            bd=0,
            cursor="hand2"
        )
        self.fit_button.pack(side=tk.LEFT)

        self.fit_ok_button = tk.Button(
            self.fit_frame,
            text="OK",
            command=self.execute_fit_plot,
            width=5,
            bg="#7897b9",
            fg=TEXT_LIGHT,
            bd=0,
            cursor="hand2"
        )
        self.fit_ok_button.pack(side=tk.RIGHT, padx=6)


        # ==================================================
        # LEFT PANEL : CLEAR
        # ==================================================

        self.clear_button = tk.Button(
            self.control_frame,
            text="Clear",
            command=self.clear_plot,
            width=30,
            bg="#d77f5f",
            fg=TEXT_LIGHT,
            activebackground="#a1887f",
            bd=0,
            cursor="hand2"
        )
        self.clear_button.pack(pady=4)


        # ==================================================
        # LEFT PANEL : QUIT
        # ==================================================

        self.quit_button = tk.Button(
            self.control_frame,
            text="Quit",
            command=self.root.destroy,
            width=30,
            bg="#a03737",
            fg=TEXT_LIGHT,
            activebackground="#8d5b5b",
            bd=0,
            cursor="hand2"
        )
        self.quit_button.pack(pady=(4,8))

        # ==================================================
        # Analysis menu
        # ==================================================

        self.analysis_menu = Menu(self.root, tearoff=0)

        # 1st submenu: ToF Experiment
        self.tof_submenu = Menu(self.analysis_menu, tearoff=0)
        self.analysis_menu.add_cascade(label="Time-of-Flight (ToF) Experiment", menu=self.tof_submenu)
        
        # Add existing ToF options
        tof_options = [
            ("1 - Grouping Comparison", "1"),
            ("2 - Dead Time Correction", "2"),
            ("3 - Efficiency vs Energy", "3"),
            ("4 - Efficiency vs ToF", "4"),
            ("5 - Maxwellian Comparison", "5"),
            ("9 - Reactor Power Comparison", "9"),
            ("10 - Reactor Power vs Neutron Rate", "10"),
            ("11 - Cross Section", "11"),
        ]
        for label, p_id in tof_options:
            self.tof_submenu.add_command(
                label=label, 
                command=lambda l=label, i=p_id: self._set_current_analysis(l, i)
            )

        # 2nd submenu: NAA Experiment
        self.naa_submenu = Menu(self.analysis_menu, tearoff=0)
        self.analysis_menu.add_cascade(label="Neutron Activation Analysis (NAA)", menu=self.naa_submenu)
        
        # Example of NAA options (to adapt based on plot_NAA.py functions)
        naa_options = [
            ("Gamma Spectrum Analysis", "NAA_1"),
            ("Decay Curve Fitting", "NAA_2"),
            ("Elemental Concentration", "NAA_3"),
        ]
        for label, p_id in naa_options:
            self.naa_submenu.add_command(
                label=label, 
                command=lambda l=label, i=p_id: self._set_current_analysis(l, i)
            )

        # ==================================================
        # Fit menu
        # ==================================================

        self.fit_menu = Menu(self.root, tearoff=0)

        fit_options = [
            ("6 - Least Square Maxwell Fit", "6"),
            ("7.1 - Curve Fit Maxwell (ToF view)", "7.1"),
            ("7.2 - Curve Fit Maxwell (ToF + Epi)", "7.2"),
            ("8.1 - Energy Spectrum (ToF convert)", "8.1"),
            ("8.2 - Energy Spectrum (ToF + Epi)", "8.2"),
        ]

        for label, p_id in fit_options:
            self.fit_menu.add_command(
                label=label,
                command=lambda l=label, i=p_id: self._set_fit_plot(l, i)
            )
            

        # LEFT PANEL: COMPACT AND DISTINCT ACTIONS
        # ==================================================
        self.btn_frame = tk.Frame(self.control_frame, bg=BG_DARK)
        self.btn_frame.pack(pady=2)
        
        self.display_t_min = tk.DoubleVar(value=150)
        self.display_t_max = tk.DoubleVar(value=3700)

        self.display_E_min = tk.DoubleVar(value=0.003)
        self.display_E_max = tk.DoubleVar(value=0.2)
        self.display_y_min = tk.DoubleVar(value=PARAMS.get('y_min', 0.0))
        self.display_y_max = tk.DoubleVar(value=PARAMS.get('y_max', 20.0))
        
        limits_frame = tk.LabelFrame(
            self.control_frame,
            text="Display Limits",
            bg=BG_DARK,
            fg="#d3d3d3",
            font=FONT_BOLD
        )
        
        limits_frame.pack(fill="x", padx=10, pady=10)
        
        # ==================================================
        # t_min
        # ==================================================
        
        tk.Label(
            limits_frame,
            text="t_min (µs)",
            bg=BG_DARK,
            fg=TEXT_LIGHT
        ).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        entry_tmin = tk.Entry(
            limits_frame,
            textvariable=self.display_t_min,
            width=10
        )
        
        entry_tmin.grid(row=0, column=1, padx=5)
        
        entry_tmin.bind("<Return>", self.update_live_zoom)
        
        tk.Scale(
            limits_frame,
            from_=0,
            to=1000,
            resolution=10,
            orient="horizontal",
            variable=self.display_t_min,
            command=self.update_live_zoom,
            length=120,
            sliderlength=18,
            showvalue=False,
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            highlightthickness=0
        ).grid(row=0, column=2)
        
        
        # ==================================================
        # t_max
        # ==================================================
        
        tk.Label(
            limits_frame,
            text="t_max (µs)",
            bg=BG_DARK,
            fg=TEXT_LIGHT
        ).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        entry_tmax = tk.Entry(
            limits_frame,
            textvariable=self.display_t_max,
            width=10
        )
        
        entry_tmax.grid(row=1, column=1, padx=5)
        
        entry_tmax.bind("<Return>", self.update_live_zoom)
        
        tk.Scale(
            limits_frame,
            from_=0,
            to=5000,
            resolution=10,
            orient="horizontal",
            variable=self.display_t_max,
            command=self.update_live_zoom,
            length=120,
            sliderlength=18,
            showvalue=False,
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            highlightthickness=0
        ).grid(row=1, column=2)
        
        
        # ==================================================
        # E_min
        # ==================================================
        
        tk.Label(
            limits_frame,
            text="E_min (eV)",
            bg=BG_DARK,
            fg=TEXT_LIGHT
        ).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        
        entry_emin = tk.Entry(
            limits_frame,
            textvariable=self.display_E_min,
            width=10
        )
        
        entry_emin.grid(row=2, column=1, padx=5)
        
        entry_emin.bind("<Return>", self.update_live_zoom)
        
        tk.Scale(
            limits_frame,
            from_=0.001,
            to=0.01,
            resolution=0.001,
            orient="horizontal",
            variable=self.display_E_min,
            command=self.update_live_zoom,
            length=120,
            sliderlength=18,
            showvalue=False,
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            highlightthickness=0
        ).grid(row=2, column=2)
        
        
        # ==================================================
        # E_max
        # ==================================================
        
        tk.Label(
            limits_frame,
            text="E_max (eV)",
            bg=BG_DARK,
            fg=TEXT_LIGHT
        ).grid(row=3, column=0, padx=5, pady=2, sticky="w")
        
        entry_emax = tk.Entry(
            limits_frame,
            textvariable=self.display_E_max,
            width=10
        )
        
        entry_emax.grid(row=3, column=1, padx=5)
        
        entry_emax.bind("<Return>", self.update_live_zoom)
        
        tk.Scale(
            limits_frame,
            from_=0.01,
            to=1,
            resolution=0.01,
            orient="horizontal",
            variable=self.display_E_max,
            command=self.update_live_zoom,
            length=120,
            sliderlength=18,
            showvalue=False,
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            highlightthickness=0
        ).grid(row=3, column=2)

        # ==================================================
        # Y_min
        # ==================================================
        tk.Label(
            limits_frame,
            text="Y min",
            bg=BG_DARK,
            fg=TEXT_LIGHT
        ).grid(row=4, column=0, padx=5, pady=2, sticky="w")

        entry_ymin = tk.Entry(
            limits_frame,
            textvariable=self.display_y_min,
            width=10
        )
        entry_ymin.grid(row=4, column=1, padx=5)
        entry_ymin.bind("<Return>", self.on_change_y_limits)

        tk.Scale(
            limits_frame,
            from_=0.0,
            to=100.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.display_y_min,
            command=self.on_change_y_limits,
            length=120,
            sliderlength=18,
            showvalue=False,
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            highlightthickness=0
        ).grid(row=4, column=2)

        # ==================================================
        # Y_max
        # ==================================================
        tk.Label(
            limits_frame,
            text="Y max",
            bg=BG_DARK,
            fg=TEXT_LIGHT
        ).grid(row=5, column=0, padx=5, pady=2, sticky="w")

        entry_ymax = tk.Entry(
            limits_frame,
            textvariable=self.display_y_max,
            width=10
        )
        entry_ymax.grid(row=5, column=1, padx=5)
        entry_ymax.bind("<Return>", self.on_change_y_limits)

        tk.Scale(
            limits_frame,
            from_=0.1,
            to=200.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.display_y_max,
            command=self.on_change_y_limits,
            length=120,
            sliderlength=18,
            showvalue=False,
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            highlightthickness=0
        ).grid(row=5, column=2)

        # ==================================================
        # INITIAL EMPTY PLOT (PLACEHOLDER)
        # ==================================================
        self.clear_plot()

        # ==================================================
        # TAB 2: PHYSICAL PARAMETERS PANEL
        # ==================================================
        self.param_frame = tk.LabelFrame(
            self.tab_config,
            text=" Global Settings & Physical Constants ",
            bg="#f8f9fa",
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=20
        )
        self.param_frame.pack(padx=40, pady=40, fill=tk.BOTH, expand=True)

        # --- Material Section ---
        tk.Label(self.param_frame, text="Thickness (cm) :", bg="#f8f9fa", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", pady=10)
        self.thickness_var = tk.StringVar(value=str(PARAMS["thickness"]))
        self.thickness_entry = tk.Entry(self.param_frame, textvariable=self.thickness_var, width=15, font=("Segoe UI", 11))
        self.thickness_entry.grid(row=0, column=1, pady=10, padx=10)

        tk.Label(self.param_frame, text="Atom Density (cm⁻³) :", bg="#f8f9fa", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w", pady=10)
        self.density_var = tk.StringVar(value=f"{PARAMS['atom_density']:.2e}")
        self.density_entry = tk.Entry(self.param_frame, textvariable=self.density_var, width=15, font=("Segoe UI", 11))
        self.density_entry.grid(row=1, column=1, pady=10, padx=10)

        # --- Energy Bounds Section (E_min / E_max) ---
        tk.Label(self.param_frame, text="E min (eV) :", bg="#f8f9fa", font=("Segoe UI", 11)).grid(row=2, column=0, sticky="w", pady=10)
        self.emin_var = tk.StringVar(value=str(PARAMS["E_min"]))
        self.emin_entry = tk.Entry(self.param_frame, textvariable=self.emin_var, width=15, font=("Segoe UI", 11))
        self.emin_entry.grid(row=2, column=1, pady=10, padx=10)

        tk.Label(self.param_frame, text="E max (eV) :", bg="#f8f9fa", font=("Segoe UI", 11)).grid(row=3, column=0, sticky="w", pady=10)
        self.emax_var = tk.StringVar(value=str(PARAMS["E_max"]))
        self.emax_entry = tk.Entry(self.param_frame, textvariable=self.emax_var, width=15, font=("Segoe UI", 11))
        self.emax_entry.grid(row=3, column=1, pady=10, padx=10)

        # --- Time Bounds Section (t_min / t_max) ---
        tk.Label(self.param_frame, text="t min :", bg="#f8f9fa", font=("Segoe UI", 11)).grid(row=4, column=0, sticky="w", pady=10)
        self.tmin_var = tk.StringVar(value=str(PARAMS["t_min"]))
        self.tmin_entry = tk.Entry(self.param_frame, textvariable=self.tmin_var, width=15, font=("Segoe UI", 11))
        self.tmin_entry.grid(row=4, column=1, pady=10, padx=10)

        tk.Label(self.param_frame, text="t max :", bg="#f8f9fa", font=("Segoe UI", 11)).grid(row=5, column=0, sticky="w", pady=10)
        self.tmax_var = tk.StringVar(value=str(PARAMS["t_max"]))
        self.tmax_entry = tk.Entry(self.param_frame, textvariable=self.tmax_var, width=15, font=("Segoe UI", 11))
        self.tmax_entry.grid(row=5, column=1, pady=10, padx=10)

        # --- Save Button ---
        self.apply_params_button = tk.Button(
            self.param_frame,
            text="Apply and Save Parameters",
            command=self.save_physical_parameters,
            bg="#2ecc71",
            fg="#d3d3d3",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=5, bd=0, cursor="hand2"
        )
        self.apply_params_button.grid(row=6, column=0, columnspan=2, pady=25)

    
    # ==================================================
        # TAB 3: FIT RESULTS & STATS PANEL
        # ==================================================
        self.stats_frame = tk.LabelFrame(
            self.tab_stats,
            text=" Fit Parameters & Numerical Results ",
            bg="#f8f9fa",
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=20
        )
        self.stats_frame.pack(padx=40, pady=40, fill=tk.BOTH, expand=True)

        # Main text area to display raw results
        self.txt_stats = tk.Text(
            self.stats_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#ffffff",
            fg="#2c3e50",
            bd=1,
            highlightthickness=1
        )
        self.txt_stats.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Default initial message
        self.txt_stats.insert(tk.END, "No fit has been executed yet. Run a Maxwellian Fit to display numerical results here.")
        self.txt_stats.config(state=tk.DISABLED)

        # Button to quickly copy scientific data
        self.copy_stats_button = tk.Button(
            self.stats_frame,
            text="Copy Results to Clipboard",
            command=self.copy_stats_to_clipboard,
            bg="#34495e",
            fg="#d3d3d3",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=5,
            bd=0,
            cursor="hand2"
        )
        self.copy_stats_button.pack(side=tk.LEFT)


    # ======================================================
    # FUNCTIONS & METHODS
    # ======================================================

    def maj_ordre_selection(self, event):
        indices_actuels = list(self.file_listbox.curselection())
        if not indices_actuels:
            return       
        self.ordre_selection = [i for i in self.ordre_selection if i in indices_actuels]
        for i in indices_actuels:
            if i not in self.ordre_selection:
                self.ordre_selection.append(i)

    def load_files(self):
        if self.is_loading:
            return

        fichiers = filedialog.askopenfilenames(
            title="Select neutron data files",
            filetypes=[("Data files", "*.dat"), ("All files", "*.*")],
            initialdir="data"
        )
        if not fichiers:
            return

        # --- CREATION OF THE MULTI-FILE PROGRESS WINDOW ---
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Loading Progress")
        
        # Dynamic height calculation
        win_width = 580
        win_height = min(650, 40 + (len(fichiers) * 38))

        # 1. Get screen dimensions
        screen_width = progress_win.winfo_screenwidth()
        screen_height = progress_win.winfo_screenheight()

        # 2. Calculate X and Y coordinates to center the window
        x = (screen_width // 2) - (win_width // 2)
        y = (screen_height // 2) - (win_height // 2)

        # 3. Apply size AND position to the window
        progress_win.geometry(f"{win_width}x{win_height}+{x}+{y}")
        progress_win.resizable(False, False)
        progress_win.transient(self.root)
        progress_win.grab_set()

        # Grid configuration for fluid alignment
        progress_win.columnconfigure(0, weight=3)  # Filename column
        progress_win.columnconfigure(1, weight=4)  # Progressbar column
        progress_win.columnconfigure(2, weight=1)  # Percentage string column

        rows_tracker = []
        
        # Generation of all UI rows simultaneously before calculation starts
        for idx, fichier in enumerate(fichiers):
            filename = os.path.basename(fichier)
            # Truncate filename if too long to keep the layout clean
            display_name = filename if len(filename) <= 28 else filename[:25] + "..."
            
            # Left: Filename Label
            lbl_name = tk.Label(progress_win, text=display_name, anchor="w", font=("Segoe UI", 9))
            lbl_name.grid(row=idx, column=0, padx=12, pady=6, sticky="ew")
            
            # Middle: Dedicated File Progressbar
            p_bar = ttk.Progressbar(progress_win, orient="horizontal", mode="determinate", maximum=100)
            p_bar.grid(row=idx, column=1, padx=10, pady=6, sticky="ew")
            p_bar["value"] = 0
            
            # Right: Percentage / Status Label
            lbl_pct = tk.Label(progress_win, text="0%", width=12, anchor="w", font=("Segoe UI", 9, "bold"), fg="#7f8c8d")
            lbl_pct.grid(row=idx, column=2, padx=8, pady=6, sticky="w")
            
            rows_tracker.append({
                "p_bar": p_bar,
                "lbl_pct": lbl_pct,
                "lbl_name": lbl_name,
                "filename": filename,
                "path": fichier
            })

        # Render layout shell
        progress_win.update()

        try:
            self.is_loading = True
            self.root.config(cursor="watch")
            
            for item in rows_tracker:
                # Highlight active row in Blue
                item["lbl_name"].config(fg="#2980b9")
                item["lbl_pct"].config(text="Loading...", fg="#2980b9")
                progress_win.update()
                
                filename = item["filename"]
                fichier = item["path"]
                
                if filename in self.datasets:
                    # Cache hit setup (instantly filled)
                    item["p_bar"]["value"] = 100
                    item["lbl_pct"].config(text="100% (Cached)", fg="#27ae60")
                    item["lbl_name"].config(fg="#27ae60")
                    progress_win.update()
                    continue  
                
                try:
                    # Atomic file calculation
                    self.datasets[filename] = process_neutron_data(fichier)
                    self.file_listbox.insert(tk.END, filename)
                    
                    # Update row layout to Green 100% on success
                    item["p_bar"]["value"] = 100
                    item["lbl_pct"].config(text="100%", fg="#27ae60")
                    item["lbl_name"].config(fg="#27ae60")
                except Exception as e:
                    # Update row layout to Red on failure
                    item["lbl_pct"].config(text="Failed", fg="#e74c3c")
                    item["lbl_name"].config(fg="#e74c3c")
                    messagebox.showerror("Parsing Error", f"Could not parse file:\n{filename}\n\n{e}")
                
                progress_win.update()
                
            # Brief pause at the end so the user can visualize all 100% marks completed
            progress_win.after(500)
            
        finally:
            self.is_loading = False
            self.root.config(cursor="")
            self.status_label.config(text="Ready")
            progress_win.destroy()

    def clear_cache(self):
        if messagebox.askyesno("Clear Cache", "Are you sure you want to unload all files and clear cache?"):
            self.datasets.clear()
            self.file_listbox.delete(0, tk.END)
            self.ordre_selection.clear()
            self.plot_history.clear()
            self.history_combobox.set("No history yet")
            self.history_combobox.configure(values=[])
            self.clear_plot()


    def _ask_reference_files(self, multiple=False):
        """Handles file explorer opening for reference files (Plots 11 and 12)."""
        if not messagebox.askyesno("Reference File", "Do you want to compare with a reference file?"):
            return ""
        
        options = {
            "title": "Select reference cross section file(s)" if multiple else "Select reference cross section file",
            "filetypes": [("Data files", "*.dat *.txt"), ("All files", "*.*")],
            "initialdir": "data"
        }
        
        if multiple:
            paths = filedialog.askopenfilenames(**options)
            return list(paths) if paths else ""
        else:
            path = filedialog.askopenfilename(**options)
            return path if path else ""
        

    # def execute_plot(self):
    #     numero_plot = self.selected_plot_id
    #     choix = self.selected_plot_label.get()
        
    #     if not self.datasets:
    #         messagebox.showwarning("Warning", "Please load data files first.")
    #         return
        
    #     if not self.ordre_selection:
    #         messagebox.showwarning("Selection Error", "Please select at least one file in the list to plot.")   
    #         return

    #     fichiers = [self.file_listbox.get(i) for i in self.ordre_selection]

    #     try:
    #         self.clear_plot()
            
    #         # Import du module complet pour utiliser getattr dynamiquement
    #         import plot as pt
    #         base_kwargs = {"frame": self.plot_frame}

    #         # --- ROUTING OF NAA PHENOMENA ---
    #         if numero_plot.startswith("NAA_"):
    #             import plot_NAA as pt_naa
    #             if numero_plot == "NAA_1":
    #                 self.current_fig = pt_naa.plot_gamma_spectrum(fichiers, self.datasets, **base_kwargs)
    #             elif numero_plot == "NAA_2":
    #                 self.current_fig = pt_naa.plot_decay_curve(fichiers, self.datasets, **base_kwargs)
    #             elif numero_plot == "NAA_3":
    #                 self.current_fig = pt_naa.plot_concentration(fichiers, self.datasets, **base_kwargs)

    #         # --- FAMILY 1: Standard Graphs (including Plot 6) ---
    #         elif numero_plot in ["1", "2", "3", "4", "5", "6", "9", "10"]:
    #             func = getattr(pt, f"plot_{numero_plot}")
    #             self.current_fig = func(fichiers, self.datasets, **base_kwargs)
                
    #             # Specific extraction for Plot 6 (Grid Search Maxwell Fit)
    #             if numero_plot == "6":
    #                 from physics import fit_maxwellian_grid_search
                    
    #                 summary = "==================================================\n"
    #                 summary += " GRID SEARCH MAXWELLIAN FIT RESULTS\n"
    #                 summary += "==================================================\n\n"
                    
    #                 # On recalcule rapidement les constantes pour les afficher dans l'IHM en anglais
    #                 for nom in fichiers:
    #                     data = self.datasets[nom]
    #                     mask = (data['ToF'] >= PARAMS['t_min']) & (data['ToF'] <= PARAMS['t_max'])
    #                     ToF_fit = data['ToF'][mask]
    #                     flux_fit = data['flux_tof'][mask]
                        
    #                     T_best, erreur_min = fit_maxwellian_grid_search(
    #                         ToF_fit, flux_fit, data['meta']['path_length']
    #                     )
                        
    #                     summary += f"Dataset File : {nom}\n"
    #                     summary += f"  -> Best Fit Temperature : {T_best:.2f} K\n"
    #                     summary += f"  -> Minimum Residual Error : {erreur_min:.2e}\n"
    #                     summary += f"  -> Active Time Range : {PARAMS['t_min']*1e6:.1f} to {PARAMS['t_max']*1e6:.1f} µs\n\n"
                    
    #                 self.update_stats_display(summary)
                
    #         # --- FAMILY 2: Advanced Maxwell Adjustments (7.1, 7.2) ---
    #         elif numero_plot in ["7.1", "7.2"]:
    #             self.current_fig, self.fit_results = pt.plot_7(
    #                 fichiers, self.datasets, choice_sub=float(numero_plot), **base_kwargs
    #             )
                
    #             # Reading and formatting of fit_results dictionary returned by plot_7
    #             if self.fit_results:
    #                 summary = "==================================================\n"
    #                 summary += f" ADVANCED CURVE FIT RESULTS (Plot {numero_plot})\n"
    #                 summary += "==================================================\n\n"
    #                 summary += f"Primary Analyzed File : {fichiers[0]}\n\n"
    #                 summary += "Extracted Physical Constants & Parameters :\n"
                    
    #                 # Key mapping for clean English display
    #                 key_mapping = {
    #                     "T_1": "Pure Maxwellian Temperature (T1)",
    #                     "T_1_epi": "Maxwellian + Epithermal Temperature (T1_epi)",
    #                     "r_squared_1": "R² Coefficient (Pure Maxwellian)",
    #                     "r_squared_2": "R² Coefficient (Grouped Maxwellian)",
    #                     "r_squared_1_epi": "R² Coefficient (Maxwellian + Epithermal)",
    #                     "a1_tof_pure_1": "Amplitude Factor a1 (Model 1)",
    #                     "a1_tof_pure_2": "Amplitude Factor a1 (Model 2)",
    #                     "Ed_epi_1": "Epithermal Cutoff Energy (Ed)",
    #                     "b_epi_1": "Epithermal Parameter b",
    #                     "beta_epi_1": "Epithermal Parameter beta"
    #                 }
                    
    #                 for key, val in self.fit_results.items():
    #                     # Filter numpy prediction arrays to keep only scalars
    #                     if isinstance(val, (int, float, np.float64, np.int64)):
    #                         label_en = key_mapping.get(key, key)
    #                         summary += f"  -> {label_en} : {val:.4f}\n"
                            
    #                 self.update_stats_display(summary)
                
    #         # --- FAMILY 3: Energy Spectra (8.1, 8.2) ---
    #         elif numero_plot in ["8.1", "8.2"]:
    #             if self.fit_results is None:
    #                 messagebox.showwarning("Warning", "Please execute plot 7 first to compute fit results.")
    #                 return
                
    #             self.current_fig = pt.plot_8(
    #                 fichiers, self.datasets, self.fit_results, choice_sub=float(numero_plot), **base_kwargs
    #             )
                
    #             # Optional: Display text reminder that statistics from this plot stem from fit 7
    #             summary = "==================================================\n"
    #             summary += f" ENERGY SPECTRUM MODELING (Plot {numero_plot})\n"
    #             summary += "==================================================\n\n"
    #             summary += f"Based on prior fit parameters from: {fichiers[0]}\n"
    #             summary += "Plots display converted Time-of-Flight configurations into Energy scale (eV).\n"
    #             summary += "Review 'Fit Results & Stats' tab parameters for exact scaling coefficients."
    #             self.update_stats_display(summary)
                
    #         # Family 4: Cross Sections (11, 12) - Requires physical parameters and references
    #         elif numero_plot in ["11", "12"]:
    #             fichier_ref = self._ask_reference_files(multiple=(numero_plot == "11"))
    #             func = getattr(pt, f"plot_{numero_plot}")
    #             self.current_fig = func(
    #                 fichiers, self.datasets,  
    #                 fichier_ref=fichier_ref, 
    #                 **base_kwargs
    #             )

    #         self._process_plot_statistics(numero_plot, fichiers, choix)
    #         self.update_live_zoom()
    #         self._reconfigure_y_sliders() # Call to external function
            
    #         # Capture current text stats content and save everything as a clean snapshot
    #         current_stats = self.txt_stats.get("1.0", tk.END).strip()
    #         self.add_to_history(choix, fichiers, figure_obj=self.current_fig, stats_text=current_stats)

    #     except Exception as e:
    #         messagebox.showerror("Plot Error", str(e))

    def execute_flux_tof(self):
        """Plot the corrected neutron flux in the Time-of-Flight domain."""

        if not self.datasets:
            messagebox.showwarning("Warning", "Please load data files first.")
            return

        if not self.ordre_selection:
            messagebox.showwarning(
                "Selection Error",
                "Please select at least one file."
            )
            return

        fichiers = [self.file_listbox.get(i) for i in self.ordre_selection]

        self.clear_plot()

        import plot as pt

        self.current_fig = pt.plot_flux_tof(
            fichiers,
            self.datasets,
            frame=self.plot_frame
        )

        self.update_live_zoom()
        self._reconfigure_y_sliders()

    def execute_flux_energy(self):
        """Plot the corrected neutron flux in the Energy domain."""

        if not self.datasets:
            messagebox.showwarning("Warning", "Please load data files first.")
            return

        if not self.ordre_selection:
            messagebox.showwarning(
                "Selection Error",
                "Please select at least one file."
            )
            return

        fichiers = [self.file_listbox.get(i) for i in self.ordre_selection]

        self.clear_plot()

        import plot as pt

        self.current_fig = pt.plot_flux_energy(
            fichiers,
            self.datasets,
            frame=self.plot_frame
        )

        self.update_live_zoom()
        self._reconfigure_y_sliders()

    
    def _reconfigure_y_sliders(self):
        """Automatically adjusts Y slider bounds relative to graph data."""
        if not hasattr(self, 'current_fig') or not self.current_fig.axes:
            return

        ax_auto = self.current_fig.axes[0]
        ymin_auto, ymax_auto = ax_auto.get_ylim()
        
        # 1. Temporary deactivation of Y locking
        self.apply_y_limits = False 
        
        # 2. Calculate the actual data range of the graph
        plage = ymax_auto - ymin_auto
        if plage <= 0: 
            plage = 1.0
        
        # Ultra-fine step based on new large movement range
        pas_haute_precision = (plage * 2) / 2000.0  
        
        # 3. Detection and individual centering of each slider in the middle (50%) of its travel
        def reconfigurer_les_sliders(parent):
            for child in parent.winfo_children():
                if isinstance(child, tk.Scale):
                    try:
                        var_liee = str(child.cget('variable'))
                        if var_liee == str(self.display_y_min):
                            # Initial ymin_auto value placed exactly in the center
                            child.configure(from_=ymin_auto - plage, to=ymin_auto + plage, resolution=pas_haute_precision, digits=7)
                        elif var_liee == str(self.display_y_max):
                            # Initial ymax_auto value placed exactly in the center
                            child.configure(from_=ymax_auto - plage, to=ymax_auto + plage, resolution=pas_haute_precision, digits=7)
                    except Exception:
                        pass
                if child.winfo_children():
                    reconfigurer_les_sliders(child)

        # Apply physical reconfiguration
        reconfigurer_les_sliders(self.root)
        
        # 4. Injection of initial values
        self.display_y_min.set(ymin_auto)
        self.display_y_max.set(ymax_auto)



    def _process_plot_statistics(self, numero_plot, fichiers, choix):
        """Handles extraction, translation, and display of numerical data according to plot type."""
        # Default case if no results are expected
        if numero_plot not in ["6", "7.1", "7.2", "8.1", "8.2"]:
            self.update_stats_display("No fit has been executed yet. Run a Maxwellian Fit to display numerical results here.")
            return

        summary = "==================================================\n"
        
        # --- Formatage pour le Plot 6 ---
        if numero_plot == "6":
            from physics import fit_maxwellian_grid_search
            summary += " GRID SEARCH MAXWELLIAN FIT RESULTS\n"
            summary += "==================================================\n\n"
            for nom in fichiers:
                data = self.datasets[nom]
                mask = (data['ToF'] >= PARAMS['t_min']) & (data['ToF'] <= PARAMS['t_max'])
                T_best, erreur_min = fit_maxwellian_grid_search(data['ToF'][mask], data['flux_tof'][mask], data['meta']['path_length'])
                
                summary += f"Dataset File : {nom}\n"
                summary += f"  -> Best Fit Temperature : {T_best:.2f} K\n"
                summary += f"  -> Minimum Residual Error : {erreur_min:.2e}\n"
                summary += f"  -> Active Time Range : {PARAMS['t_min']*1e6:.1f} to {PARAMS['t_max']*1e6:.1f} µs\n\n"

        # --- Formatage pour les Plots 7.1 et 7.2 ---
        elif numero_plot in ["7.1", "7.2"] and self.fit_results:
            summary += f" ADVANCED CURVE FIT RESULTS (Plot {numero_plot})\n"
            summary += "==================================================\n\n"
            summary += f"Primary Analyzed File : {fichiers[0]}\n\n"
            summary += "Extracted Physical Constants & Parameters :\n"
            
            key_mapping = {
                "T_1": "Pure Maxwellian Temperature (T1)",
                "T_1_epi": "Maxwellian + Epithermal Temperature (T1_epi)",
                "r_squared_1": "R² Coefficient (Pure Maxwellian)",
                "r_squared_2": "R² Coefficient (Grouped Maxwellian)",
                "r_squared_1_epi": "R² Coefficient (Maxwellian + Epithermal)",
                "a1_tof_pure_1": "Amplitude Factor a1 (Model 1)",
                "a1_tof_pure_2": "Amplitude Factor a1 (Model 2)",
                "Ed_epi_1": "Epithermal Cutoff Energy (Ed)",
                "b_epi_1": "Epithermal Parameter b",
                "beta_epi_1": "Epithermal Parameter beta"
            }
            for key, val in self.fit_results.items():
                if isinstance(val, (int, float, np.float64, np.int64)):
                    summary += f"  -> {key_mapping.get(key, key)} : {val:.4f}\n"

        # --- Formatage pour les Plots 8.1 et 8.2 ---
        elif numero_plot in ["8.1", "8.2"]:
            summary += f" ENERGY SPECTRUM MODELING (Plot {numero_plot})\n"
            summary += "==================================================\n\n"
            summary += f"Based on prior fit parameters from: {fichiers[0]}\n"
            summary += "Plots display converted Time-of-Flight configurations into Energy scale (eV).\n"
            summary += "Review 'Fit Results & Stats' tab parameters for exact scaling coefficients."

        # Envoi final vers le widget de l'IHM
        self.update_stats_display(summary)

            
    def add_to_history(self, plot_name, files, figure_obj, stats_text=""):
        """Adds a successful plot session snapshot directly to the history memory."""
        import datetime
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Adding a timestamp ensures unique labels even with identical files
        affichage_label = f"[{current_time}] Plot {plot_name.split('-')[0].strip()} ({len(files)} files) - {', '.join(files[:2])}"
        if len(files) > 2:
            affichage_label += "..."

        # CRITICAL: We need a deep copy/unlinked snapshot of the figure to prevent overwrites
        # We achieve this by saving the figure state temporarily or archiving it
        import pickle
        try:
            # Pickle serializes the figure state, creating a completely isolated clone
            fig_snapshot = pickle.loads(pickle.dumps(figure_obj))
        except Exception:
            # Fallback if pickle fails due to specific active Tkinter widget bindings
            fig_snapshot = figure_obj

        # Store the isolated snapshot and the text statistics
        self.plot_history.append({
            "nom_complet": plot_name,
            "fichiers": files,
            "label": affichage_label,
            "figure": fig_snapshot,
            "stats_text": stats_text
        })
        
        # Update history dropdown selection view
        liste_labels = [item["label"] for item in self.plot_history]
        self.history_combobox.configure(values=liste_labels)
        self.history_combobox.set(affichage_label)

    def replay_plot_from_history(self, event):
        """Replays the exact graphical snapshot directly from the stored Matplotlib Figure object."""
        label_selectionne = self.history_combobox.get()
        
        # Find the selected item inside the history collection
        historique_item = None
        for item in self.plot_history:
            if item["label"] == label_selectionne:
                historique_item = item
                break
                
        if not historique_item or "figure" not in historique_item:
            return
            
        saved_fig = historique_item["figure"]
        nom_complet = historique_item["nom_complet"]
        fichiers_sauvegardes = historique_item["fichiers"]
        
        # Synchronize selection text tracking variables
        self.selected_plot_label.set(nom_complet)
        self.selected_plot_id = nom_complet.split('-')[0].strip()
        
        # Synchronize UI listbox file selection indicators
        self.ordre_selection = []
        self.file_listbox.selection_clear(0, tk.END)
        for f in fichiers_sauvegardes:
            for idx in range(self.file_listbox.size()):
                if self.file_listbox.get(idx) == f:
                    self.ordre_selection.append(idx)
                    self.file_listbox.select_set(idx) 

        # Wipe out old plot frame widgets to prevent overlay issues
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
            
        # Re-embed the native saved Matplotlib figure container directly into the GUI
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        canvas = FigureCanvasTkAgg(saved_fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Re-attach standard navigation toolbar control elements
        toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Update references and restore text stats snapshot if available
        self.current_fig = saved_fig
        if "stats_text" in historique_item:
            self.update_stats_display(historique_item["stats_text"])
            
    def save_physical_parameters(self):
        """Converts and saves GUI inputs into the global dictionary."""
        try:
            # Systematic float conversion to secure calculations
            PARAMS["thickness"] = float(self.thickness_var.get())
            PARAMS["E_min"] = float(self.emin_var.get())
            PARAMS["E_max"] = float(self.emax_var.get())
            PARAMS["t_min"] = float(self.tmin_var.get())
            PARAMS["t_max"] = float(self.tmax_var.get())
            
            # float() natively supports scientific notation (e.g. 2.3e22)
            PARAMS["atom_density"] = float(self.density_var.get())
            
            messagebox.showinfo("Success", "Parameters successfully applied to global config.")
            
        except ValueError as e:
            # Safety if user makes input error (e.g. a letter or empty field)
            messagebox.showerror("Parsing Error", f"Please enter valid numerical values.\nDetails: {e}")

    def clear_plot(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
            
        fig = Figure(figsize=(12, 8), dpi=100)
        fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.current_fig = fig
        self.apply_y_limits = False

    def show_analysis_menu(self):

        x = self.select_plot_button.winfo_rootx()
        y = self.select_plot_button.winfo_rooty() + self.select_plot_button.winfo_height()

        self.analysis_menu.post(x, y)

    def _set_analysis_plot(self, label, analysis_id):

        self.selected_analysis_id = analysis_id
        self.selected_plot_label.set(label)

    def show_fit_menu(self):

        x = self.fit_button.winfo_rootx()
        y = self.fit_button.winfo_rooty() + self.fit_button.winfo_height()

        self.fit_menu.post(x, y)


    def _set_fit_plot(self, label, fit_id):

        self.selected_fit_id = fit_id
        self.selected_fit_label.set(label)

    def _set_current_analysis(self, label, analysis_id):
        """Updates selection variables and modifies button text."""
        self.selected_analysis_id = analysis_id
        self.selected_plot_label.set(label)

        
    def action_grouper_fichiers(self):
        """Triggers file explorer opening for file grouping (Option 98)"""
        if self.is_loading:
            return

        print("Opening file explorer via menu...")
        fichiers_selectionnes = filedialog.askopenfilenames(
            title="Select the files you want to group together",
            filetypes=[("Data files", "*.dat *.txt"), ("All files", "*.*")]
        )
        
        if fichiers_selectionnes:
            liste_chemins = list(fichiers_selectionnes)
            print(f"Selected {len(liste_chemins)} files to merge.")
            try:
                # Locking and status display for heavy I/O merge processing
                self.is_loading = True
                self.root.config(cursor="watch")
                self.status_label.config(text="Merging data files... Please wait.")
                self.root.update()
                
                grouped_file(liste_chemins)
            finally:
                self.is_loading = False
                self.root.config(cursor="")
                self.status_label.config(text="Ready")
        else:
            print("Operation cancelled: No files selected.\n")
            
    def save_current_plot(self):
        """Opens a file dialog to save the currently displayed Matplotlib figure."""
        if not hasattr(self, 'current_fig') or self.current_fig is None:
            messagebox.showwarning("Save Error", "No active plot available to save.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Plot As",
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("PDF Document", "*.pdf"),
                ("All Files", "*.*")
            ]
        )

        if file_path:
            try:
                # Saves figure with high resolution and tight borders
                self.current_fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", "Plot saved successfully!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save plot:\n{e}")
                
    def export_current_data(self):
        """Scans the active Matplotlib figure, extracts curves and their uncertainties (if any), and exports to CSV."""
        if not hasattr(self, 'current_fig') or self.current_fig is None:
            messagebox.showwarning("Export Error", "No active plot available. Please generate a plot first.")
            return

        axes = self.current_fig.get_axes()
        available_curves = {}

        for ax in axes:
            panel_title = ax.get_title() or ax.get_ylabel() or "Plot"
            x_label = ax.get_xlabel() or "X_Axis"
            y_label = ax.get_ylabel() or "Y_Axis"
            
            # --- DRAWER 1: Classic Lines (No uncertainties) ---
            for line in ax.get_lines():
                label = line.get_label()
                if label and not label.startswith('_'):
                    unique_name = f"Panel: '{panel_title}' ➔ Line: {label}"
                    available_curves[unique_name] = {
                        "x": line.get_xdata(),
                        "y": line.get_ydata(),
                        "yerr": None, # No uncertainty here
                        "x_header": x_label.replace(" ", "_"),
                        "y_header": y_label.replace(" ", "_")
                    }
            
            # --- DRAWER 2: Error Bars (Uncertainty Extraction) ---
            for container in ax.containers:
                label = container.get_label()
                if label and not label.startswith('_'):
                    if hasattr(container, 'lines') and len(container.lines) > 0:
                        data_line = container.lines[0]
                        x_data = data_line.get_xdata()
                        y_data = data_line.get_ydata()
                        
                        # Geometric extraction of vertical error bars
                        y_err = None
                        if len(container.lines) > 2 and container.lines[2]:
                            try:
                                v_bars = container.lines[2][0] # Collection of vertical bars
                                paths = v_bars.get_paths()
                                if paths and len(paths) == len(x_data):
                                    # Calculate half-height of each error segment (y_max - y_min) / 2
                                    y_err = np.array([(p.vertices[1, 1] - p.vertices[0, 1]) / 2.0 for p in paths])
                            except Exception:
                                y_err = None # Secure fallback in case of complex geometry

                        name_suffix = " (with uncertainties)" if y_err is not None else ""
                        unique_name = f"Panel: '{panel_title}' ➔ Data: {label}{name_suffix}"
                        
                        available_curves[unique_name] = {
                            "x": x_data,
                            "y": y_data,
                            "yerr": y_err, # Storage of uncertainty array
                            "x_header": x_label.replace(" ", "_"),
                            "y_header": y_label.replace(" ", "_")
                        }

            # --- DRAWER 3: Point Clouds (No standard uncertainties) ---
            for collection in ax.collections:
                label = collection.get_label()
                if label and not label.startswith('_'):
                    offsets = collection.get_offsets()
                    if len(offsets) > 0:
                        unique_name = f"Panel: '{panel_title}' ➔ Scatter: {label}"
                        available_curves[unique_name] = {
                            "x": offsets[:, 0],
                            "y": offsets[:, 1],
                            "yerr": None,
                            "x_header": x_label.replace(" ", "_"),
                            "y_header": y_label.replace(" ", "_")
                        }

        if not available_curves:
            messagebox.showwarning("Export Error", "No labeled data curves found in the current plot.")
            return

        # 2. Window Layout Selection
        export_win = tk.Toplevel(self.root)
        export_win.title("Select Curve to Export")
        export_win.geometry("520x150")
        export_win.resizable(False, False)
        export_win.transient(self.root)
        export_win.grab_set()
        
        sw, sh = export_win.winfo_screenwidth(), export_win.winfo_screenheight()
        export_win.geometry(f"520x150+{sw//2 - 260}+{sh//2 - 75}")

        tk.Label(export_win, text="Select the specific curve you want to extract:", font=("Segoe UI", 10, "bold")).pack(pady=(15, 5))
        
        curve_combobox = ttk.Combobox(export_win, values=list(available_curves.keys()), state="readonly", width=65)
        curve_combobox.pack(pady=5, padx=15)
        curve_combobox.current(0)

        # 3. Dynamic physical CSV saving
        def trigger_save():
            selected_curve_name = curve_combobox.get()
            curve_data = available_curves[selected_curve_name]
            
            file_path = filedialog.asksaveasfilename(
                title="Save Curve Data",
                defaultextension=".csv",
                filetypes=[("CSV Tables", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if not file_path:
                return

            try:
                # Verification: Do we have uncertainties to export?
                if curve_data["yerr"] is not None:
                    # Compilation of 3 columns: X, Y, and Yerr
                    matrix = np.column_stack((curve_data["x"], curve_data["y"], curve_data["yerr"]))
                    header_string = f"{curve_data['x_header']},{curve_data['y_header']},{curve_data['y_header']}_Uncertainty"
                else:
                    # Classic fallback to 2 columns: X and Y
                    matrix = np.column_stack((curve_data["x"], curve_data["y"]))
                    header_string = f"{curve_data['x_header']},{curve_data['y_header']}"
                
                np.savetxt(file_path, matrix, delimiter=",", header=header_string, comments="")
                messagebox.showinfo("Success", "Curve data extracted and saved successfully!")
                export_win.destroy()
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export data:\n{e}")

        btn_frame = tk.Frame(export_win)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="Export Selection", command=trigger_save, bg="#2ecc71", fg="#d3d3d3", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=export_win.destroy, bg="#7f8c8d", fg="#d3d3d3", font=("Segoe UI", 9), bd=0, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        
    def validate_ranges(self):
        # ===============================
        # TOF (Preserved)
        # ===============================
        tmin = max(0, min(self.display_t_min.get(), 5000))
        tmax = max(0, min(self.display_t_max.get(), 5000))
    
        if tmin >= tmax:
            tmin = tmax - 1
    
        self.display_t_min.set(tmin)
        self.display_t_max.set(tmax)
    
        # ===============================
        # ENERGY (Preserved)
        # ===============================
        emin = max(0.001, min(self.display_E_min.get(), 0.01))
        emax = max(0.01, min(self.display_E_max.get(), 2))
    
        if emin >= emax:
            emin = emax * 0.5
    
        self.display_E_min.set(emin)
        self.display_E_max.set(emax)

        # ===============================
        # Y AXIS INTELLIGENT
        # ===============================
        ymin = self.display_y_min.get()
        ymax = self.display_y_max.get()

        if ymin >= ymax:
            ymin = ymax * 0.99

        self.display_y_min.set(ymin)
        self.display_y_max.set(ymax)        

    def on_change_y_limits(self, val=None):
        self.apply_y_limits = True
        self.update_live_zoom(val)

    def update_live_zoom(self, val=None):
        if not hasattr(self, 'current_fig') or self.current_fig is None:
            return

        try:
            self.validate_ranges()

            tmin = self.display_t_min.get()
            tmax = self.display_t_max.get()
            emin = self.display_E_min.get()
            emax = self.display_E_max.get()
            ymin = self.display_y_min.get()
            ymax = self.display_y_max.get()

            for ax in self.current_fig.axes:
                xlabel = ax.get_xlabel().lower()

                if "time" in xlabel or "tof" in xlabel:
                    ax.set_xlim(tmin, tmax)
                elif "energy" in xlabel or "ev" in xlabel:
                    ax.set_xlim(emin, emax)

                # Applies Y limits only if user moved a Y slider
                if getattr(self, 'apply_y_limits', False):
                    ax.set_ylim(ymin, ymax)

            self.current_fig.canvas.draw_idle()

        except Exception as e:
            print(f"Error update_live_zoom : {e}")

    
    def update_stats_display(self, text_content):
        """Dynamically updates the statistics text area on the statistics tab."""
        self.txt_stats.config(state=tk.NORMAL)
        self.txt_stats.delete("1.0", tk.END)
        self.txt_stats.insert(tk.END, text_content)
        self.txt_stats.config(state=tk.DISABLED)

    def copy_stats_to_clipboard(self):
        """Copies text area content directly to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.txt_stats.get("1.0", tk.END).strip())
        messagebox.showinfo("Success", "Results successfully copied to clipboard.")

    def _prepare_plot_execution(self):
        """
        Perform common checks and initialize plot execution.
        Returns (fichiers, base_kwargs) or None if execution must stop.
        """

        if not self.datasets:
            messagebox.showwarning(
                "Warning",
                "Please load data files first."
            )
            return None

        if not self.ordre_selection:
            messagebox.showwarning(
                "Selection Error",
                "Please select at least one file in the list to plot."
            )
            return None

        fichiers = [
            self.file_listbox.get(i)
            for i in self.ordre_selection
        ]

        self.clear_plot()

        base_kwargs = {
            "frame": self.plot_frame
        }

        return fichiers, base_kwargs

    def _finalize_plot_execution(self, numero_plot, fichiers, choix):
        """
        Common operations after a successful plot.
        """

        self._process_plot_statistics(
            numero_plot,
            fichiers,
            choix
        )

        self.update_live_zoom()

        self._reconfigure_y_sliders()

        current_stats = self.txt_stats.get(
            "1.0",
            tk.END
        ).strip()

        self.add_to_history(
            choix,
            fichiers,
            figure_obj=self.current_fig,
            stats_text=current_stats
        )



    def execute_analysis_plot(self):

        numero_plot = self.selected_analysis_id
        choix = self.selected_plot_label.get()

        prepared = self._prepare_plot_execution()

        if prepared is None:
            return

        fichiers, base_kwargs = prepared

        import plot as pt

        try:

            self.clear_plot()
            
            # ==========================================================
            # NAA ANALYSIS
            # ==========================================================

            if numero_plot.startswith("NAA_"):

                import plot_NAA as pt_naa

                if numero_plot == "NAA_1":
                    self.current_fig = pt_naa.plot_gamma_spectrum(
                        fichiers,
                        self.datasets,
                        **base_kwargs
                    )

                elif numero_plot == "NAA_2":
                    self.current_fig = pt_naa.plot_decay_curve(
                        fichiers,
                        self.datasets,
                        **base_kwargs
                    )

                elif numero_plot == "NAA_3":
                    self.current_fig = pt_naa.plot_concentration(
                        fichiers,
                        self.datasets,
                        **base_kwargs
                    )

            # ==========================================================
            # STANDARD PLOTS
            # ==========================================================

            elif numero_plot in ["1", "2", "3", "4", "5", "9", "10"]:

                func = getattr(pt, f"plot_{numero_plot}")

                self.current_fig = func(
                    fichiers,
                    self.datasets,
                    **base_kwargs
                )

            # ==========================================================
            # CROSS SECTIONS
            # ==========================================================

            elif numero_plot in ["11"]:

                fichier_ref = self._ask_reference_files(
                    multiple=(numero_plot == "11")
                )

                func = getattr(pt, f"plot_{numero_plot}")

                self.current_fig = func(
                    fichiers,
                    self.datasets,
                    fichier_ref=fichier_ref,
                    **base_kwargs
                )

            # ==========================================================
            # COMMON POST-PROCESSING
            # ==========================================================

            self._finalize_plot_execution(
                numero_plot,
                fichiers,
                choix
            )

        except Exception as e:
            messagebox.showerror(
                "Plot Error",
                str(e)
            )

    def execute_fit_plot(self):

        numero_plot = self.selected_fit_id
        choix = self.fit_button.cget("text")

        prepared = self._prepare_plot_execution()

        if prepared is None:
            return

        fichiers, base_kwargs = prepared

        import plot as pt

        try:

            self.clear_plot()

            # ==========================================================
            # PLOT 6 : GRID SEARCH MAXWELL FIT
            # ==========================================================

            if numero_plot == "6":

                self.current_fig = pt.plot_6(
                    fichiers,
                    self.datasets,
                    **base_kwargs
                )

                from physics import fit_maxwellian_grid_search

                summary = "==================================================\n"
                summary += " GRID SEARCH MAXWELLIAN FIT RESULTS\n"
                summary += "==================================================\n\n"

                for nom in fichiers:

                    data = self.datasets[nom]

                    mask = (
                        (data["ToF"] >= PARAMS["t_min"])
                        &
                        (data["ToF"] <= PARAMS["t_max"])
                    )

                    ToF_fit = data["ToF"][mask]
                    flux_fit = data["flux_tof"][mask]

                    T_best, erreur_min = fit_maxwellian_grid_search(
                        ToF_fit,
                        flux_fit,
                        data["meta"]["path_length"]
                    )

                    summary += f"Dataset File : {nom}\n"
                    summary += f"  -> Best Fit Temperature : {T_best:.2f} K\n"
                    summary += f"  -> Minimum Residual Error : {erreur_min:.2e}\n"
                    summary += (
                        f"  -> Active Time Range : "
                        f"{PARAMS['t_min']*1e6:.1f} "
                        f"to "
                        f"{PARAMS['t_max']*1e6:.1f} µs\n\n"
                    )

                self.update_stats_display(summary)

            # ==========================================================
            # PLOT 7
            # ==========================================================

            elif numero_plot in ["7.1", "7.2"]:

                self.current_fig, self.fit_results = pt.plot_7(
                    fichiers,
                    self.datasets,
                    choice_sub=float(numero_plot),
                    **base_kwargs
                )

                if self.fit_results:

                    summary = "==================================================\n"
                    summary += f" ADVANCED CURVE FIT RESULTS (Plot {numero_plot})\n"
                    summary += "==================================================\n\n"

                    summary += f"Primary Analyzed File : {fichiers[0]}\n\n"

                    summary += (
                        "Extracted Physical Constants & Parameters :\n"
                    )

                    key_mapping = {

                        "T_1":
                            "Pure Maxwellian Temperature (T1)",

                        "T_1_epi":
                            "Maxwellian + Epithermal Temperature (T1_epi)",

                        "r_squared_1":
                            "R² Coefficient (Pure Maxwellian)",

                        "r_squared_2":
                            "R² Coefficient (Grouped Maxwellian)",

                        "r_squared_1_epi":
                            "R² Coefficient (Maxwellian + Epithermal)",

                        "a1_tof_pure_1":
                            "Amplitude Factor a1 (Model 1)",

                        "a1_tof_pure_2":
                            "Amplitude Factor a1 (Model 2)",

                        "Ed_epi_1":
                            "Epithermal Cutoff Energy (Ed)",

                        "b_epi_1":
                            "Epithermal Parameter b",

                        "beta_epi_1":
                            "Epithermal Parameter beta"

                    }

                    for key, val in self.fit_results.items():

                        if isinstance(
                            val,
                            (int, float, np.float64, np.int64)
                        ):

                            label_en = key_mapping.get(key, key)

                            summary += (
                                f"  -> {label_en} : {val:.4f}\n"
                            )

                    self.update_stats_display(summary)

            # ==========================================================
            # PLOT 8
            # ==========================================================

            elif numero_plot in ["8.1", "8.2"]:

                if self.fit_results is None:

                    messagebox.showwarning(
                        "Warning",
                        "Please execute Plot 7 before Plot 8."
                    )
                    return

                self.current_fig = pt.plot_8(
                    fichiers,
                    self.datasets,
                    self.fit_results,
                    choice_sub=float(numero_plot),
                    **base_kwargs
                )

                summary = "==================================================\n"
                summary += (
                    f" ENERGY SPECTRUM MODELING (Plot {numero_plot})\n"
                )
                summary += "==================================================\n\n"

                summary += (
                    f"Based on prior fit parameters from : "
                    f"{fichiers[0]}\n\n"
                )

                summary += (
                    "Plots display converted Time-of-Flight "
                    "configurations into Energy scale (eV).\n"
                )

                summary += (
                    "Review 'Fit Results & Stats' tab "
                    "parameters for exact scaling coefficients."
                )

                self.update_stats_display(summary)

            # ==========================================================
            # COMMON POST PROCESSING
            # ==========================================================

            self._finalize_plot_execution(
                numero_plot,
                fichiers,
                choix
            )

        except Exception as e:

            messagebox.showerror(
                "Plot Error",
                str(e)
            )

    
    def _show_markdown_file(self, title, filename):
        """
        Display a Markdown help file in a read-only window.
        """

        filepath = Path(__file__).parent / "user_guide" / filename

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

        except FileNotFoundError:
            messagebox.showerror(
                "Documentation Error",
                f"Unable to find:\n{filepath}"
            )
            return

        # ==========================
        # Window
        # ==========================

        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("900x700")

        txt = tk.Text(
            window,
            wrap="word",
            font=("Segoe UI", 10)
        )

        scrollbar = tk.Scrollbar(
            window,
            command=txt.yview
        )

        txt.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)

        # ==========================
        # Styles
        # ==========================

        txt.tag_configure(
            "h1",
            font=("Segoe UI", 18, "bold"),
            spacing1=15,
            spacing3=10
        )

        txt.tag_configure(
            "h2",
            font=("Segoe UI", 14, "bold"),
            spacing1=12,
            spacing3=8
        )

        txt.tag_configure(
            "h3",
            font=("Segoe UI", 12, "bold"),
            spacing1=8,
            spacing3=5
        )

        txt.tag_configure(
            "bold",
            font=("Segoe UI", 10, "bold")
        )

        txt.tag_configure(
            "italic",
            font=("Segoe UI", 10, "italic")
        )

        txt.tag_configure(
            "code",
            font=("Consolas", 10),
            background="#f3f3f3"
        )

        txt.tag_configure(
            "bullet",
            lmargin1=25,
            lmargin2=45
        )

        txt.tag_configure(
            "link",
            foreground="blue",
            underline=True
        )

        # ==========================
        # Markdown parser
        # ==========================

        pattern = r"(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\))"

        for line in text.splitlines():

            # ---------- Headers ----------

            if line.startswith("# "):
                txt.insert("end", line[2:] + "\n", "h1")
                continue

            elif line.startswith("## "):
                txt.insert("end", line[3:] + "\n", "h2")
                continue

            elif line.startswith("### "):
                txt.insert("end", line[4:] + "\n", "h3")
                continue

            # ---------- Horizontal rule ----------

            elif line.strip() == "---":
                txt.insert(
                    "end",
                    "────────────────────────────────────────────────────────────\n"
                )
                continue

            # ---------- Bullet list ----------

            elif line.startswith("- "):
                line = "• " + line[2:]

            # ---------- Numbered list ----------

            m = re.match(r"^(\d+)\.\s+(.*)", line)
            if m:
                line = f"{m.group(1)}. {m.group(2)}"

            # ---------- Inline formatting ----------

            pos = 0

            for match in re.finditer(pattern, line):

                start, end = match.span()

                txt.insert("end", line[pos:start])

                token = match.group()

                # Bold

                if token.startswith("**"):
                    txt.insert(
                        "end",
                        token[2:-2],
                        "bold"
                    )

                # Italic

                elif token.startswith("*"):
                    txt.insert(
                        "end",
                        token[1:-1],
                        "italic"
                    )

                # Code

                elif token.startswith("`"):
                    txt.insert(
                        "end",
                        token[1:-1],
                        "code"
                    )

                # Markdown link

                elif token.startswith("["):

                    label = re.search(r"\[(.*?)\]", token).group(1)

                    txt.insert(
                        "end",
                        label,
                        "link"
                    )

                pos = end

            txt.insert("end", line[pos:] + "\n")

        txt.config(state="disabled")

    def show_user_guide(self):
        self._show_markdown_file("User Guide", "user_guide.md")
        
    def show_workflow(self):
        self._show_markdown_file("Workflow", "work_flow.md")

    def show_plot_reference(self):
        self._show_markdown_file("Plot Reference", "plot_reference.md")

    def show_about(self):
        self._show_markdown_file("About", "about.md")