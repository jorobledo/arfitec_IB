import tkinter as tk
from tkinter import ttk
import os
import numpy as np
import matplotlib.pyplot as plt
from physics_NAA import PARAMS, get_R, get_flux, get_lambda, model_tof_epi_NAA
from physics import integrate_thermal_epithermal_flux



# def plot_counts(file_path):
#     """
#     Plots the experimental count rate as a function of energy.
#     file_path: path to .dat file (col 0: energy, col 1: count rate)
#     """
#     # Load data from the two columns
#     data = np.loadtxt(file_path)
#     energy = data[:, 0]
#     cts_rate = data[:, 1]
    
#     fig, ax = plt.subplots(figsize=(8, 5))
    
#     ax.plot(energy, cts_rate, '-', color='tab:red', linewidth=1.5, label='Experimental Data')
    
#     ax.set_xlabel('Energy (eV)')
#     ax.set_ylabel('Count Rate (cps)')
#     ax.set_title('Experimental Count Rate vs Energy')
    
#     ax.grid(True, linestyle='--', alpha=0.6)
#     ax.legend(loc='best')
    
#     plt.tight_layout()
#     plt.show()

# def plot_flux(file_path):
#     """
#     Plots the thermal and epithermal flux profiles.
#     pos: list/array of irradiation positions, phi_th/phi_epi: calculated fluxes
#     """
#     data = np.loadtxt(file_path)
#     count = 

#     print (get_flux(get_R(), get_R()))  # Example usage of get_flux function
    # fig, ax = plt.subplots(figsize=(8, 5))
    
    # ax.plot(pos, phi_th, 'o-', color='tab:blue', label=r'$\phi_{th}$ (thermal)')
    # ax.plot(pos, phi_epi, 's-', color='tab:orange', label=r'$\phi_{epi}$ (epithermal)')
    
    # ax.set_xlabel('Irradiation Position')
    # ax.set_ylabel(r'Flux (n $\cdot$ cm$^{-2}$ $\cdot$ s$^{-1}$)')
    # ax.set_title('Neutron Flux Profile (Mn)')
    
    # ax.grid(True, linestyle='--', alpha=0.6)
    # ax.legend(loc='best')
    
    # plt.tight_layout()
    # plt.savefig('flux_profile.png', dpi=300)
    # plt.show()

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
    table.insert("", "end", values=("ToF Spectrometry (Integration)", f"{phi_th_tof:.4e}", f"{phi_epi_tof:.4e}"))
    table.insert("", "end", values=("Flux Ratio (NAA / ToF)", f"{ratio_th:.4f}", f"{ratio_epi:.4f}"))

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

    counts = np.asarray(counts)

    # Energy axis (1 channel = 1 keV)
    energy = np.arange(len(counts), dtype=float)

    # Statistical uncertainty
    sigma = np.sqrt(counts)

    # ---------------- Plot ----------------

    fig, ax = plt.subplots(figsize=(10, 6))

    # Histogram
    ax.step(energy, counts,
            where="mid",
            color="royalblue",
            linewidth=1.5,
            label="Spectrum")

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
    ax.set_yscale("log")

    plt.tight_layout()
    plt.show()

    return fig


