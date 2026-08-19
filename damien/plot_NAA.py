import tkinter as tk
from tkinter import ttk
import os
import numpy as np
import matplotlib.pyplot as plt
from physics_NAA import PARAMS, get_R, get_flux, get_lambda, model_tof_epi_NAA, compute_NAA_flux_spectrum
from physics import integrate_thermal_epithermal_flux
from plot import _integrer_canvas
from pathlib import Path


def compare_flux(fichiers, datasets, frame=None):
    """
    Computes, compares and displays physical flux values in a structured table.
    Compares Neutron Activation Analysis (NAA) calculations with ToF integration.
    """
    if frame is not None:
        for widget in frame.winfo_children():
            widget.destroy()

    # --- 1. PHYSICAL COMPUTATIONS ---
    # A. NAA Flux Calculations
    # For NAA, we calculate R and R_Cd using physical defaults.
    # Replace the arguments of get_R with your experimental counts/times (t_i, t_d, t_m) if needed.
    try:
        r_bare = get_R(counts=66000, t_i=12360, t_d=3120, t_m=3600, m=PARAMS["m_mn"])  # Example placeholder physical values
        r_cadmium = get_R(counts=2700, t_i=17160    , t_d=1200, t_m=(54000), m=PARAMS["m_mn_cd"])  # Example placeholder physical values
        phi_th_naa, phi_epi_naa = get_flux(r_bare, r_cadmium)
    except Exception as e:
        # Fallback values to prevent GUI crashes if inputs are missing
        phi_th_naa, phi_epi_naa = 0.0, 0.0

    # B. TOF Spectrometry Integration Flux Calculations
    # We aggregate and average integrated fluxes across all currently selected active data files
    integrated_th_list = []
    integrated_epi_list = []

    for nom in fichiers:
        data = datasets[nom]
        if "ToF" in data and "flux_tof_ungrouped" in data:
            th_val, epi_val = integrate_thermal_epithermal_flux(data["ToF"], data["flux_tof_ungrouped"])
            integrated_th_list.append(th_val)
            integrated_epi_list.append(epi_val)

    phi_th_tof = np.mean(integrated_th_list) if integrated_th_list else 0.0
    phi_epi_tof = np.mean(integrated_epi_list) if integrated_epi_list else 0.0

    # C. Ratio Calculations (NAA / TOF)
    ratio_th = phi_th_naa / phi_th_tof if phi_th_tof > 0 else 0.0
    ratio_epi = phi_epi_naa / phi_epi_tof if phi_epi_tof > 0 else 0.0


    # --- 2. GUI TABLE DISPLAY SYSTEM (Tkinter Treeview inside frame) ---
    # We embed a high-contrast tabular dataset visualization right inside the drawing frame
    main_container = tk.Frame(frame, bg="#ffffff")
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Title Banner
    title_label = tk.Label(
        main_container, 
        text="FLUX CALIBRATION & COMPARISON RESULTS", 
        font=("Segoe UI", 12, "bold"), 
        bg="#ffffff", 
        fg="#2c3e50"
    )
    title_label.pack(pady=(0, 15))

    # Treeview Table configuration
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)

    cols = ("Metric", "Thermal Flux (n/cm²/s)", "Epithermal Flux (n/cm²/s)")
    table = ttk.Treeview(main_container, columns=cols, show="headings", height=4)
    table.pack(fill=tk.BOTH, expand=True)

    # Define Columns
    table.heading("Metric", text="Methodology Spectrum")
    table.heading("Thermal Flux (n/cm²/s)", text="Thermal Flux (n/cm²/s)")
    table.heading("Epithermal Flux (n/cm²/s)", text="Epithermal Flux (n/cm²/s)")

    table.column("Metric", width=250, anchor="w")
    table.column("Thermal Flux (n/cm²/s)", width=220, anchor="center")
    table.column("Epithermal Flux (n/cm²/s)", width=220, anchor="center")

    # Insert Data rows
    table.insert("", "end", values=("Neutron Activation Analysis (NAA)", f"{phi_th_naa:.4e}", f"{phi_epi_naa:.4e}"))
    table.insert("", "end", values=("ToF Spectrometry (Integration)", f"{phi_th_tof:.4e}", "None"))
    table.insert("", "end", values=("Flux Ratio (NAA / ToF)", f"{ratio_th:.4f}", "None"))

    # Simple text info box below table
    info_box = tk.Label(
        main_container,
        text="* ToF values represent average integrated fluxes of selected datasets.\n"
             "NAA values are determined via Mn-55 activation equations.",
        font=("Segoe UI", 9, "italic"),
        bg="#ffffff",
        fg="#7f8c8d",
        justify="left"
    )
    info_box.pack(pady=(10, 0), anchor="w")

    # We return an empty figure or None because we drew directly in Tkinter widgets
    # This prevents Matplotlib from printing a blank figure underneath
    fig = plt.figure(figsize=(1, 1))
    plt.close(fig) # Keep pyplot manager memory clean
    return None


def plot_spectrum_spe(fichier, frame=None):
    """
    Read a .Spe spectrum and plot the counts as a function of energy.
    """

    counts = []

    with open(fichier, "r") as f:
        lines = f.readlines()

    # Locate the data block
    start = None
    n_channels = None

    for i, line in enumerate(lines):
        if "$DATA:" in line:
            start = i + 2               # next line contains "first last"
            first, last = map(int, lines[i + 1].split())
            n_channels = last - first + 1
            break

    if start is None:
        raise ValueError("No $DATA section found in the .Spe file.")

    for line in lines[start:start + n_channels]:
        counts.append(float(line.strip()))

    fact = 847 / 1652

    counts = np.asarray(counts)

    # Energy axis (1 channel = 1 keV)
    energy = np.arange(len(counts), dtype=float) * fact

    # Statistical uncertainty
    sigma = np.sqrt(counts)

    # ---------------- Plot ----------------

    fig, ax = plt.subplots(12,5)

    # Histogram
    ax.step(energy, counts, where="mid", color="navy", label='Spectrum')
    ax.fill_between(energy, counts, step="mid", alpha=0.4)

    # Error bars
    ax.errorbar(
        energy,
        counts,
        yerr=sigma,
        fmt="none",
        ecolor="black",
        elinewidth=0.6,
        alpha=0.5,
        capsize=0,
        label=r"Statistical uncertainty ($\sqrt{N}$)"
    )

    ax.set_xlabel("Energy (keV)", fontsize=13)
    ax.set_ylabel("Counts", fontsize=13)
    ax.set_title("Gamma spectrum", fontsize=15)

    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.legend()
    # ax.set_yscale("log")

    plt.tight_layout()
    _integrer_canvas(fig, frame)
    return fig

def plot_Ge_efficiency(fichier, frame=None):

    # ==========================================================
    # Files
    # ==========================================================
    BASE_DIR = Path(__file__).parent
    NAA_DIR = BASE_DIR / "NAA"

    file_9_95 = NAA_DIR / "efi_HPGe_d9_95cm.dat"
    file_25_15 = NAA_DIR / "efi_HPGe_d25_15cm.dat"

    # ==========================================================
    # Load data
    # ==========================================================
    data_9_95 = np.loadtxt(file_9_95)
    data_25_15 = np.loadtxt(file_25_15)

    E_9_95 = data_9_95[:, 0]
    eff_9_95 = data_9_95[:, 1]

    E_25_15 = data_25_15[:, 0]
    eff_25_15 = data_25_15[:, 1]

    # ==========================================================
    # Target energy
    # ==========================================================
    E_target = 834.8  # keV

    # Linear interpolation in energy
    efficiency_9_95 = np.interp(
        E_target,
        E_9_95,
        eff_9_95
    )

    efficiency_25_15 = np.interp(
        E_target,
        E_25_15,
        eff_25_15
    )

    # ==========================================================
    # Linear interpolation in distance
    # ==========================================================
    d1 = 9.95
    d2 = 25.15
    d_target = 15.5

    efficiency_15_5 = (
        efficiency_9_95
        + (efficiency_25_15 - efficiency_9_95)
        * (d_target - d1)
        / (d2 - d1)
    )

    # ==========================================================
    # Plot
    # ==========================================================
    fig, ax = plt.subplots(figsize=(12, 5))

    # ----------------------------------------------------------
    # Efficiency curves
    # ----------------------------------------------------------
    ax.plot(
        E_9_95,
        eff_9_95,
        label="d = 9.95 cm"
    )

    ax.plot(
        E_25_15,
        eff_25_15,
        label="d = 25.15 cm"
    )

    # ----------------------------------------------------------
    # Points at 834.8 keV
    # ----------------------------------------------------------
    ax.scatter(
        E_target,
        efficiency_9_95,
        s=70,
        zorder=5
    )

    ax.scatter(
        E_target,
        efficiency_25_15,
        s=70,
        zorder=5
    )

    # ----------------------------------------------------------
    # Vertical line at 834.8 keV
    # ----------------------------------------------------------
    ax.axvline(
        E_target,
        linestyle="--",
        alpha=0.5
    )

    # ----------------------------------------------------------
    # Distance interpolation
    # ----------------------------------------------------------
    ax.plot(
        [E_target, E_target],
        [efficiency_9_95, efficiency_25_15],
        linestyle="--",
        alpha=0.7,
        label="Distance interpolation"
    )

    # ----------------------------------------------------------
    # Interpolated point at 15.5 cm
    # ----------------------------------------------------------
    ax.scatter(
        E_target,
        efficiency_15_5,
        s=130,
        marker="x",
        zorder=6,
        label="Interpolated value (15.5 cm)"
    )

    # ----------------------------------------------------------
    # Annotation
    # ----------------------------------------------------------
    ax.annotate(
        f"d = 15.5 cm\n"
        f"E = 834.8 keV\n"
        f"ε = {efficiency_15_5:.5g}",
        xy=(E_target, efficiency_15_5),
        xytext=(25, 25),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->"),
        fontsize=10
    )

    # ==========================================================
    # Formatting
    # ==========================================================
    ax.set_xscale("log")

    ax.set_xlabel("Energy (keV)")
    ax.set_ylabel("Efficiency")
    ax.set_title("HPGe detector efficiency")

    ax.grid(
        True,
        which="both",
        alpha=0.3
    )

    ax.legend()

    plt.tight_layout()
    _integrer_canvas(fig, frame)

    return fig


def plot_NAA_flux_modelisation(fichier, frame=None):

    T=293.0
    n_points = 1000
    E_min=1e-3
    E_max=1e3
    alpha = 0.0

    # ==========================================================
    # 1. PHYSICAL COMPUTATIONS
    # ==========================================================

    try:

        # ------------------------------------------------------
        # Reaction rate - bare sample
        # ------------------------------------------------------
        r_bare = get_R(
            counts=66000,
            t_i=12360,
            t_d=3120,
            t_m=3600,
            m=PARAMS["m_mn"]
        )

        # ------------------------------------------------------
        # Reaction rate - Cd-covered sample
        # ------------------------------------------------------
        r_cadmium = get_R(
            counts=2700,
            t_i=17160,
            t_d=1200,
            t_m=54000,
            m=PARAMS["m_mn_cd"]
        )

        # ------------------------------------------------------
        # Thermal and epithermal fluxes from NAA
        # ------------------------------------------------------
        phi_th_naa, phi_epi_naa = get_flux(
            r_bare,
            r_cadmium
        )

    except Exception as e:

        print(f"NAA flux calculation error: {e}")

        # Fallback values to prevent GUI crash
        phi_th_naa = 0.0
        phi_epi_naa = 0.0

    # ----------------------------------------------------------
    # Energy grid
    # ----------------------------------------------------------
    E = np.logspace(
        np.log10(E_min),
        np.log10(E_max),
        n_points
    )

    # ----------------------------------------------------------
    # Compute flux contributions
    # ----------------------------------------------------------
    Phi_th, Phi_epi, Phi_total = compute_NAA_flux_spectrum(
        Phi_th_NAA=phi_th_naa,
        Phi_epi_NAA=phi_epi_naa,
        E=E,
        T=T,
        alpha=alpha
    )

    # ----------------------------------------------------------
    # Plot
    # ----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        E,
        Phi_th,
        alpha=0.5,
        linewidth=2,
        label="Thermal"
    )

    ax.plot(
        E,
        Phi_epi,
        alpha=0.5,
        linewidth=2,
        label=rf"Epithermal ($\alpha={alpha}$)"
    )

    ax.plot(
        E,
        Phi_total,
        alpha=1.0,
        linewidth=2.5,
        label="Total"
    )

    # ----------------------------------------------------------
    # Formatting
    # ----------------------------------------------------------

    ax.set_xlabel("Energy (eV)")
    ax.set_ylabel(r"$\Phi(E)$")

    ax.set_title("Neutron flux trend from NAA")

    ax.grid(
        True,
        which="both",
        alpha=0.3
    )

    ax.legend()

    plt.tight_layout()
    _integrer_canvas(fig, frame)

    return fig