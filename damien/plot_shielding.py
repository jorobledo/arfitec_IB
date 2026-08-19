import tkinter as tk
from tkinter import ttk
import os
import re
from matplotlib.widgets import RangeSlider
import numpy as np
import matplotlib.pyplot as plt
from physics_NAA import get_R, get_flux, get_lambda, model_tof_epi_NAA
from physics import PARAMS, integrate_thermal_epithermal_flux, masse_n, eV
from plot import _integrer_canvas
from config import PARAMS
from physics_shielding import (
    build_sigma_mix_from_files,
    average_transmission,
    load_cross_section,
    average_transmission_ref,
    transmission_vs_energy,
    transmission_vs_energy_ref,
)
from scipy.interpolate import interp1d
from pathlib import Path
from physics_shielding import composition_data


def plot_max_peak_concentration(
        fichiers,
        datasets,
        frame=None):
    """
    Plot the evolution of the ToF peak position
    as a function of B4C concentration.
    """

    WINDOW = 30

    THERMAL_T_MIN = 300e-6
    THERMAL_T_MAX = 2000e-6

    if frame is not None:
        for widget in frame.winfo_children():
            widget.destroy()

    concentrations = []
    tof_peak_list = []

    # ==========================================================
    # Loop over samples
    # ==========================================================

    for nom in fichiers:

        basename = os.path.basename(nom)

        if basename.lower().startswith("tl"):
                    concentration = 0.0
        else:
            try:
                concentration = float(basename.split("%")[0])
            except ValueError:
                raise ValueError(
                    f"Unable to extract the B4C concentration from the filename:\n"
                    f"{basename}\n\n"
                    "Expected filename format:\n"
                    "  tl_reference.dat\n"
                    "  10%_sample.dat\n"
                    "  25%_sample.dat"
                )

        data = datasets[nom]

        flux = data["tof_flux"]["all"]["method1"]["flux"]
        tof = data["tof_flux"]["all"]["method1"]["ToF"]

        mask = (tof >= THERMAL_T_MIN) & (tof <= THERMAL_T_MAX)

        flux = flux[mask]
        tof = tof[mask]

        if len(flux) < 10:
            continue

        # ------------------------------------------------------
        # Peak position
        # ------------------------------------------------------

        idx_max = np.argmax(flux)

        i0 = max(
            0,
            idx_max - WINDOW
        )

        i1 = min(
            len(flux),
            idx_max + WINDOW + 1
        )

        tof_peak = np.average(
            tof[i0:i1],
            weights=flux[i0:i1]
        )

        concentrations.append(concentration)
        tof_peak_list.append(tof_peak * 1e6)

    # ==========================================================
    # Sort by concentration
    # ==========================================================

    order = np.argsort(concentrations)

    concentrations = np.array(concentrations)[order]
    tof_peak_list = np.array(tof_peak_list)[order]

    # ==========================================================
    # Plot
    # ==========================================================

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        concentrations,
        tof_peak_list,
        "o-",
        linewidth=1.5,
        markersize=6
    )

    ax.set_xlabel("B$_4$C concentration (%)")
    ax.set_ylabel("Peak position (µs)")
    ax.set_title("Thermal peak position vs concentration")

    ax.grid(
        True,
        linestyle="--",
        alpha=0.5
    )

    plt.tight_layout()

    _integrer_canvas(fig, frame)

    return fig

def plot_transmission_concentration(fichiers, datasets, comparison_points=None, frame=None, **kwargs):
    """
    Plot the thermal neutron transmission as a function of B4C concentration.

    The transmission is computed as:

        T = Sum(flux_sample) / Sum(flux_reference)

    using only the thermal region.
    """

    # ==========================================================
    # Identify reference, background and samples
    # ==========================================================

    ref_file = None
    sample_files = []

    for nom in fichiers:

        basename = os.path.basename(nom).lower()

        if basename.startswith("tl"):
            ref_file = nom

        else:
            sample_files.append(nom)

    if ref_file is None:
        raise ValueError(
            "No reference file found. A filename starting with 'tl' is required."
        )

    # ----------------------------------------------------------
    # Thermal integration limits
    # ----------------------------------------------------------

    THERMAL_T_MIN = 300e-6
    THERMAL_T_MAX = 2000e-6

    if frame is not None:
        for widget in frame.winfo_children():
            widget.destroy()

    concentrations = []
    transmissions = []
    unc_transmissions = []

    # ==========================================================
    # Reference sample
    # ==========================================================

    ref = datasets[ref_file]

    flux_ref = ref["tof_flux"]["all"]["method1"]["flux"]
    unc_ref = ref["tof_flux"]["all"]["method1"]["unc"]
    tof_ref = ref["tof_flux"]["all"]["method1"]["ToF"]

    mask_ref = (tof_ref >= THERMAL_T_MIN) & (tof_ref <= THERMAL_T_MAX)

    I_ref = np.sum(flux_ref[mask_ref])

    sigma_ref = np.sqrt(np.sum(unc_ref[mask_ref]**2))

    # ==========================================================
    # Loop over all samples
    # ==========================================================

    for nom in fichiers:
        data = datasets[nom]

        flux = data["tof_flux"]["all"]["method1"]["flux"]
        unc = data["tof_flux"]["all"]["method1"]["unc"]
        tof = data["tof_flux"]["all"]["method1"]["ToF"]

        mask = (tof >= THERMAL_T_MIN) & (tof <= THERMAL_T_MAX)

        I = np.sum(flux[mask])

        sigma_I = np.sqrt(np.sum(unc[mask]**2))

        transmission = I / I_ref

        sigma_T = transmission * np.sqrt(
            (sigma_I / I) ** 2 +
            (sigma_ref / I_ref) ** 2
        )

        # ------------------------------------------------------
        # Extract concentration from filename
        # ------------------------------------------------------

        basename = os.path.basename(nom)

        if basename.lower().startswith("tl"):
            concentration = 0.0
        else:
            try:
                concentration = float(basename.split("%")[0])
            except ValueError:
                raise ValueError(
                    f"Unable to extract the B4C concentration from the filename:\n"
                    f"{basename}\n\n"
                    "Expected filename format:\n"
                    "  tl_reference.dat\n"
                    "  10%_sample.dat\n"
                    "  25%_sample.dat"
                )

        # ------------------------------------------------------
        # Store results
        # ------------------------------------------------------

        concentrations.append(concentration)
        transmissions.append(transmission)
        unc_transmissions.append(sigma_T)

    # ==========================================================
    # Sort by concentration
    # ==========================================================

    order = np.argsort(concentrations)

    concentrations = np.array(concentrations)[order]
    transmissions = np.array(transmissions)[order]
    unc_transmissions = np.array(unc_transmissions)[order]

    # ==========================================================
    # Comparison points
    # ==========================================================

    comparison_data = {}

    if comparison_points:

        for point in comparison_points:

            fichier = point["file"]
            value = point["value"]
            element = point["element"]

            data = datasets[os.path.basename(fichier)]

            flux = (
                data["tof_flux"]["all"]["method1"]["flux"]
            )

            unc = data["tof_flux"]["all"]["method1"]["unc"]

            tof = data["tof_flux"]["all"]["method1"]["ToF"]

            mask = (
                (tof >= THERMAL_T_MIN)
                &
                (tof <= THERMAL_T_MAX)
                &
                (flux > 0)
            )

            I = np.sum(flux[mask])

            sigma_I = np.sqrt(
                np.sum(unc[mask] ** 2)
            )

            transmission = I / I_ref

            sigma_T = transmission * np.sqrt(
                (sigma_I / I) ** 2 +
                (sigma_ref / I_ref) ** 2
            )

            if element not in comparison_data:
                comparison_data[element] = []

            comparison_data[element].append({
                "x": value,
                "T": transmission,
                "unc": sigma_T
            })



    # ==========================================================
    # Plot
    # ==========================================================

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.errorbar(
        concentrations,
        transmissions,
        yerr=unc_transmissions,
        xerr=0.3,
        fmt="o--",
        capsize=4,
        linewidth=1.5,
        markersize=6,
        label="B4C thermal transmission"
    )

    # ==========================================================
    # Plot comparison points
    # ==========================================================

    from scipy.interpolate import interp1d

    # Interpolation de la courbe principale T(x)
    curve_interp = interp1d(
        concentrations,
        transmissions,
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate"
    )

    # Interpolation inverse x(T)
    x_from_y = interp1d(
        transmissions[::-1],
        concentrations[::-1],
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate"
    )

    for element, points in comparison_data.items():

        for point in points:

            x_point = point["x"]
            y_point = point["T"]
            yerr = point["unc"]

            try:

                # Position sur la courbe principale ayant la même transmission
                x_intersect = float(x_from_y(y_point))

                point_artist = ax.errorbar(
                    x_point,
                    y_point,
                    yerr=yerr,
                    fmt="s",
                    capsize=4,
                    markersize=7,
                    label=(
                        f"{element} : "
                        f"x={x_point:.2f} %, "
                        f"T={y_point:.3f}, "
                        f"x_eq={x_intersect:.2f} %"
                    )
                )

                # Couleur du point
                color = point_artist[0].get_color()

                # Barre horizontale
                ax.plot(
                    [0, x_intersect],
                    [y_point, y_point],
                    color=color,
                    alpha=0.30,
                    linewidth=2
                )

                # Barre verticale
                ax.plot(
                    [x_intersect, x_intersect],
                    [0, y_point],
                    color=color,
                    alpha=0.30,
                    linewidth=2
                )

                # Marque l'intersection avec la courbe
                ax.plot(
                    x_intersect,
                    y_point,
                    marker="+",
                    markersize=12,
                    color=color,
                    alpha=0.8
                )

            except Exception as e:

                print(
                    f"Cannot determine intersection for "
                    f"{element}: {e}"
                )

    # ==========================================================
    # Theoretical transmission model
    # ==========================================================
    show_theo = kwargs.get("show_theo_transmission", True)
    if show_theo :

        # ------------------------------------------------------
        # Cross section files
        # ------------------------------------------------------
        BASE_DIR = Path(__file__).parent

        B_file  = BASE_DIR / "Shielding" / "set-tot" / "B" / "sig-tot-B.dat"
        C_file  = BASE_DIR / "Shielding" / "set-tot" / "C" / "sig-tot-C.dat"
        H_file  = BASE_DIR / "Shielding" / "set-tot" / "H" / "sig-tot-H.dat"
        O_file  = BASE_DIR / "Shielding" / "set-tot" / "O" / "sig-tot-O.dat"
        Si_file = BASE_DIR / "Shielding" / "set-tot" / "Si" / "sig-tot-Si.dat"
        Cd_file = BASE_DIR / "Shielding" / "set-tot" / "Cd" / "sig-tot-Cd.dat"

        # ------------------------------------------------------
        # Experimental incident spectrum
        # ------------------------------------------------------

        tof_ref = ref["ToF"]
        flux_ref_tof = ref["flux_tof"]

        # ------------------------------------------------------
        # Compute theoretical transmission
        # ------------------------------------------------------

        T_theory = []

        for concentration in concentrations[1:]:

            data = composition_data[concentration]

            fract_B4C, fract_PDMS, fract_SiO2, fract_MTMS = data["fract_mol"]

            atomic_density = data["atomic_density"]

            # Recompute sigma_mix for this concentration
            E_mix, sigma_mix, sigma_Cd, sigma_CH2 = build_sigma_mix_from_files(
                B_file,
                C_file,
                H_file,
                O_file,
                Si_file,
                Cd_file,
                fract_B4C,
                fract_PDMS,
                fract_SiO2,
                fract_MTMS
            )

            # --------------------------------------------------
            # Convert reference ToF -> Energy
            # --------------------------------------------------

            E_ref = ref["E"]

            # Interpolate sigma on experimental energy grid
            sigma_interp = interp1d(
                E_mix,
                sigma_mix,
                bounds_error=False,
                fill_value="0"
            )

            sigma_ref = sigma_interp(E_ref)

            # Thermal window
            E_max_thermal = 0.5 * masse_n * (1.915 / THERMAL_T_MIN)**2 / eV
            E_min_thermal = 0.5 * masse_n * (1.915 / THERMAL_T_MAX)**2 / eV
            mask = (E_ref >= E_min_thermal) & (E_ref <= E_max_thermal)

            T = average_transmission(
                0.45,
                E_ref[mask],
                sigma_ref[mask],
                flux_ref_tof[mask],
                atomic_density=atomic_density
            )

            T_theory.append(T)

        T_theory = np.array(T_theory)

        ax.plot(
            concentrations[1:],
            T_theory,
            "o--",
            color="#E69F00",
            markerfacecolor="white",
            markeredgecolor="#E69F00",
            linewidth=1.5,
            label="Beer-Lambert model"
        )

    ax.set_xlabel("B$_4$C concentration (%)")
    ax.set_ylabel("Thermal neutron transmission")
    ax.set_title("Thermal neutron transmission")

    ax.grid(True, linestyle="--", alpha=0.5)
    handles, labels = ax.get_legend_handles_labels()

    if labels:
        ax.legend()

    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()

    _integrer_canvas(fig, frame)

    return fig


def plot_transmission_concentration_tof(fichiers, datasets, frame=None):
    """
    Plot neutron transmission as a function of Time-of-Flight.

    T(ToF) = Flux_sample(ToF) / Flux_reference(ToF)

    The first selected file is assumed to be the reference and is
    therefore not displayed.
    """

    # ==========================================================
    # Identify reference, background and samples
    # ==========================================================

    ref_file = None
    sample_files = []

    for nom in fichiers:

        basename = os.path.basename(nom).lower()

        if basename.startswith("tl"):
            ref_file = nom

        else:
            sample_files.append(nom)

    if ref_file is None:
        raise ValueError(
            "No reference file found. A filename starting with 'tl' is required."
        )


    if len(fichiers) < 2:
        raise ValueError(
            "At least one reference file and one sample file are required."
        )

    if frame is not None:
        for widget in frame.winfo_children():
            widget.destroy()

    # ==========================================================
    # Reference spectrum
    # ==========================================================

    ref = datasets[ref_file]

    tof_ref = ref["tof_flux"]["all"]["method1"]["ToF"]
    flux_ref = ref["tof_flux"]["all"]["method1"]["flux"]
    unc_ref = ref["tof_flux"]["all"]["method1"]["unc"]

    # Avoid divisions by zero
    mask_ref = flux_ref > 0

    fig, ax = plt.subplots(figsize=(12, 5))

    # ==========================================================
    # Loop over samples
    # ==========================================================

    for nom in sample_files:

        data = datasets[nom]

        tof = data["tof_flux"]["all"]["method1"]["ToF"]
        flux = data["tof_flux"]["all"]["method1"]["flux"]
        unc = data["tof_flux"]["all"]["method1"]["unc"]

        threshold = 0.01 * np.max(flux_ref)

        mask = (
            (flux_ref > threshold)
            & np.isfinite(flux)
            & np.isfinite(flux_ref)
        )

        transmission = flux[mask] / flux_ref[mask]

        unc_transmission = np.abs(transmission) * np.sqrt(
            (unc[mask] / flux[mask])**2 +
            (unc_ref[mask] / flux_ref[mask])**2
        )

        basename = os.path.basename(nom)

        if basename.lower().startswith("tl"):
            concentration = 0.0
        else:
            try:
                concentration = float(basename.split("%")[0])
            except ValueError:
                raise ValueError(
                    f"Unable to extract the B4C concentration from the filename:\n"
                    f"{basename}\n\n"
                    "Expected filename format:\n"
                    "  tl_reference.dat\n"
                    "  .5_sample.dat\n"
                    "  .10_sample.dat"
                )
        print("flux min =", np.min(flux))
        print("flux_ref min =", np.min(flux_ref))
        print("nb flux < 0 :", np.sum(flux < 0))
        print("nb flux_ref < 0 :", np.sum(flux_ref < 0))
        


        lignes, caps, bars = ax.errorbar(
            tof[mask] * 1e6,      # µs
            transmission,
            yerr=unc_transmission,
            fmt='.-',
            linewidth=1,
            capsize=0,
            label=f"B$_4$C concentration = {concentration:g} %"
        )
        for bar in bars:
            bar.set_alpha(0.4)

    ax.set_xlabel("Time of Flight (µs)")
    ax.set_ylabel("Transmission")
    ax.set_title("Neutron Transmission vs Time-of-Flight")
    ax.set_ylim(-1,1)

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

    plt.tight_layout()

    _integrer_canvas(fig, frame)

    return fig



def plot_transmission_thickness(fichiers, datasets, comparison_points=None, frame=None, **kwargs):
    """
    Plot thermal neutron transmission as a function of B4C thickness.

    The first file beginning with:
        tl* -> reference
        bg* -> background

    All other files are considered samples.
    """

    import os
    import numpy as np
    import matplotlib.pyplot as plt

    THERMAL_T_MIN = PARAMS["t_min"]
    THERMAL_T_MAX = PARAMS["t_max"]

    if frame is not None:
        for widget in frame.winfo_children():
            widget.destroy()

    # ==========================================================
    # Identify reference, background and samples
    # ==========================================================

    ref_file = None
    bg_file = None
    sample_files = []

    for nom in fichiers:

        basename = os.path.basename(nom).lower()

        if basename.startswith("tl"):
            ref_file = nom

        elif basename.startswith("bg"):
            bg_file = nom

        else:
            sample_files.append(nom)

    if ref_file is None:
        raise ValueError(
            "No reference file found. A filename starting with 'tl' is required."
        )

    if bg_file is None:
        raise ValueError(
            "No background file found. A filename starting with 'bg' is required."
        )

    # ==========================================================
    # Background
    # ==========================================================

    bg_data = datasets[bg_file]

    background_level = np.mean(
        bg_data["tof_flux"]["deadtime"]["method1"]["flux"]
    )

    # ==========================================================
    # Reference
    # ==========================================================

    ref = datasets[ref_file]

    flux_ref = (
        ref["tof_flux"]["deadtime"]["method1"]["flux"]
        - background_level
    )

    unc_ref = ref["tof_flux"]["deadtime"]["method1"]["unc"]

    tof_ref = ref["tof_flux"]["deadtime"]["method1"]["ToF"]

    mask_ref = (
        (tof_ref >= THERMAL_T_MIN)
        & (tof_ref <= THERMAL_T_MAX)
        & (flux_ref > 0)
    )

    I_ref = np.sum(flux_ref[mask_ref])

    sigma_ref = np.sqrt(
        np.sum(unc_ref[mask_ref] ** 2)
    )

    # ==========================================================
    # Samples
    # ==========================================================

    thicknesses = []
    transmissions = []
    unc_transmissions = []

    for nom in [ref_file] + sample_files:

        data = datasets[nom]

        flux = (
            data["tof_flux"]["deadtime"]["method1"]["flux"]
            - background_level
        )

        unc = data["tof_flux"]["deadtime"]["method1"]["unc"]

        tof = data["tof_flux"]["deadtime"]["method1"]["ToF"]

        mask = (
            (tof >= THERMAL_T_MIN)
            & (tof <= THERMAL_T_MAX)
            & (flux > 0)
        )

        I = np.sum(flux[mask])

        sigma_I = np.sqrt(
            np.sum(unc[mask] ** 2)
        )

        transmission = I / I_ref

        sigma_T = transmission * np.sqrt(
            (sigma_I / I) ** 2 +
            (sigma_ref / I_ref) ** 2
        )

        # ------------------------------------------------------
        # Extract thickness from filename
        # Example:
        # 1_sample.dat  -> 1 mm
        # 2.5_sample.dat -> 2.5 mm
        # ------------------------------------------------------

        basename = os.path.basename(nom)

        if basename.lower().startswith("tl"):
            thickness = 0.0
        else:
            try:
                thickness = float(basename.split("mm")[0])
            except ValueError:
                raise ValueError(
                    f"Unable to extract thickness from filename:\n"
                    f"{basename}\n\n"
                    "Expected format:\n"
                    "  tl_reference.dat\n"
                    "  2.5mm_sample.dat\n"
                    "  5mm_sample.dat"
                )
        

        thicknesses.append(thickness)
        transmissions.append(transmission)
        unc_transmissions.append(sigma_T)

    # ==========================================================
    # Sort by thickness
    # ==========================================================

    order = np.argsort(thicknesses)

    thicknesses = np.array(thicknesses)[order]
    transmissions = np.array(transmissions)[order]
    unc_transmissions = np.array(unc_transmissions)[order]

    # ==========================================================
    # Comparison points
    # ==========================================================

    comparison_data = {}

    if comparison_points:

        for point in comparison_points:

            fichier = point["file"]
            value = point["value"]
            element = point["element"]

            data = datasets[os.path.basename(fichier)]

            flux = (
                data["tof_flux"]["deadtime"]["method1"]["flux"]
                - background_level
            )

            unc = data["tof_flux"]["deadtime"]["method1"]["unc"]

            tof = data["tof_flux"]["deadtime"]["method1"]["ToF"]

            mask = (
                (tof >= THERMAL_T_MIN)
                &
                (tof <= THERMAL_T_MAX)
                &
                (flux > 0)
            )

            I = np.sum(flux[mask])

            sigma_I = np.sqrt(
                np.sum(unc[mask] ** 2)
            )

            transmission = I / I_ref

            sigma_T = transmission * np.sqrt(
                (sigma_I / I) ** 2 +
                (sigma_ref / I_ref) ** 2
            )

            if element not in comparison_data:
                comparison_data[element] = []

            comparison_data[element].append({
                "x": value,
                "T": transmission,
                "unc": sigma_T
            })

    # ==========================================================
    # Plot
    # ==========================================================

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.errorbar(
        thicknesses,
        transmissions,
        yerr=unc_transmissions,
        xerr=0.1,      # modify if needed
        fmt="o--",
        capsize=4,
        linewidth=1.5,
        markersize=6,
        label="B4C transmission"
    )

    # ==========================================================
    # Plot comparison points
    # ==========================================================

    from scipy.interpolate import interp1d

    # Interpolation de la courbe principale T(x)
    curve_interp = interp1d(
        thicknesses,
        transmissions,
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate"
    )

    # Interpolation inverse x(T)
    x_from_y = interp1d(
        transmissions[::-1],
        thicknesses[::-1],
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate"
    )

    for element, points in comparison_data.items():

        for point in points:

            x_point = point["x"]
            y_point = point["T"]
            yerr = point["unc"]

            try:

                # Position sur la courbe principale ayant la même transmission
                x_intersect = float(x_from_y(y_point))

                point_artist = ax.errorbar(
                    x_point,
                    y_point,
                    yerr=yerr,
                    fmt="s",
                    capsize=4,
                    markersize=7,
                    label=(
                        f"{element} : "
                        f"x={x_point:.2f} mm, "
                        f"T={y_point:.3f}, "
                        f"x_eq={x_intersect:.2f} mm"
                    )
                )

                # Couleur du point
                color = point_artist[0].get_color()

                # Barre horizontale
                ax.plot(
                    [0, x_intersect],
                    [y_point, y_point],
                    color=color,
                    alpha=0.30,
                    linewidth=2
                )

                # Barre verticale
                ax.plot(
                    [x_intersect, x_intersect],
                    [0, y_point],
                    color=color,
                    alpha=0.30,
                    linewidth=2
                )

                # Marque l'intersection avec la courbe
                ax.plot(
                    x_intersect,
                    y_point,
                    marker="+",
                    markersize=12,
                    color=color,
                    alpha=0.8
                )

            except Exception as e:

                print(
                    f"Cannot determine intersection for "
                    f"{element}: {e}"
                )

    # ==========================================================
    # Theoretical transmission model
    # ==========================================================
    show_theo = kwargs.get("show_theo_transmission", True)

    if show_theo:

        # ------------------------------------------------------
        # Cross section files
        # ------------------------------------------------------
        BASE_DIR = Path(__file__).parent

        B_file = BASE_DIR / "Shielding" / "set-tot" / "B" / "sig-tot-B.dat"
        C_file = BASE_DIR / "Shielding" / "set-tot" / "C" / "sig-tot-C.dat"
        H_file = BASE_DIR / "Shielding" / "set-tot" / "H" / "sig-tot-H.dat"
        O_file = BASE_DIR / "Shielding" / "set-tot" / "O" / "sig-tot-O.txt"
        Si_file = BASE_DIR / "Shielding" / "set-tot" / "Si" / "sig-tot-Si.dat"
        Cd_file = BASE_DIR / "Shielding" / "set-tot" / "Cd" / "sig-tot-Cd.dat"

        ref_file = (
            BASE_DIR
            / "Shielding"
            / "set-tot"
            / "spectrum_avant_chopper.dat"
        )

        E_mix, sigma_mix, sigma_Cd, sigma_CH2 = build_sigma_mix_from_files(
            B_file,
            C_file,
            H_file,
            O_file,
            Si_file,
            Cd_file,
            0.650218276,
            0.001557414014,
            0.2690997816,
            0.07912452836
        )

        # ------------------------------------------------------
        # Experimental / simulated incident spectrum
        # ------------------------------------------------------
        E_ref, Flux_ref_simu = load_cross_section(ref_file)

        # ------------------------------------------------------
        # Interpolate cross sections on reference energy grid
        # ------------------------------------------------------
        sigma_interp = interp1d(
            E_mix,
            sigma_mix,
            bounds_error=False,
            fill_value=0.0
        )

        sigma_interp_Cd = interp1d(
            E_mix,
            sigma_Cd,
            bounds_error=False,
            fill_value=0.0
        )

        sigma_interp_CH2 = interp1d(
            E_mix,
            sigma_CH2,
            bounds_error=False,
            fill_value=0.0
        )

        sigma_mix_interp = sigma_interp(E_ref)
        sigma_Cd_interp = sigma_interp_Cd(E_ref)
        sigma_CH2_interp = sigma_interp_CH2(E_ref)

        # ------------------------------------------------------
        # Keep only valid positive energies
        # ------------------------------------------------------
        valid_mask = (
            np.isfinite(E_ref)
            & np.isfinite(Flux_ref_simu)
            & (E_ref > 0)
        )

        E_ref_valid = E_ref[valid_mask]
        Flux_ref_valid = Flux_ref_simu[valid_mask]
        sigma_mix_valid = sigma_mix_interp[valid_mask]
        sigma_Cd_valid = sigma_Cd_interp[valid_mask]
        sigma_CH2_valid = sigma_CH2_interp[valid_mask]

        # Sort according to energy
        sort_idx = np.argsort(E_ref_valid)

        E_ref_valid = E_ref_valid[sort_idx]
        Flux_ref_valid = Flux_ref_valid[sort_idx]
        sigma_mix_valid = sigma_mix_valid[sort_idx]
        sigma_Cd_valid = sigma_Cd_valid[sort_idx]
        sigma_CH2_valid = sigma_CH2_valid[sort_idx]

        # ------------------------------------------------------
        # Initial energy range
        # ------------------------------------------------------
        E_min_data = E_ref_valid.min()
        E_max_data = E_ref_valid.max()

        # Initial range = thermal window if it is inside the data range
        E_max_thermal = (
            0.5 * masse_n * (1.915 / THERMAL_T_MIN) ** 2 / eV
        )

        E_min_thermal = (
            0.5 * masse_n * (1.915 / THERMAL_T_MAX) ** 2 / eV
        )

        E_min_selected = max(E_min_data, E_min_thermal)
        E_max_selected = min(E_max_data, E_max_thermal)

        # If thermal range is not contained in the data,
        # use the complete available range
        if E_min_selected >= E_max_selected:
            E_min_selected = E_min_data
            E_max_selected = E_max_data

        # ------------------------------------------------------
        # Initial theoretical calculation
        # ------------------------------------------------------
        def compute_theoretical_transmission(
            E_min,
            E_max
        ):
            """
            Compute the theoretical transmission using only
            the selected energy interval.
            """

            energy_mask = (
                (E_ref_valid >= E_min)
                & (E_ref_valid <= E_max)
            )

            E_selected = E_ref_valid[energy_mask]
            Flux_selected = Flux_ref_valid[energy_mask]
            sigma_selected = sigma_mix_valid[energy_mask]

            sigma_Cd_selected = sigma_Cd_valid[energy_mask]
            sigma_CH2_selected = sigma_CH2_valid[energy_mask]

            # Avoid calculation if the selected interval
            # contains too few points
            if len(E_selected) < 2:
                return None

            # --------------------------------------------------
            # B4C transmission
            # --------------------------------------------------
            T_theory = []

            for thickness_mm in thicknesses:

                thickness_cm = thickness_mm / 10.0

                T = average_transmission(
                    thickness_cm,
                    E_selected,
                    sigma_selected,
                    Flux_selected,
                    atomic_density=3.35E+21
                )

                T_theory.append(T)

            T_theory = np.asarray(T_theory)

            # --------------------------------------------------
            # Polyethylene + Cd reference
            # --------------------------------------------------
            T_polyethylene = average_transmission_ref(
                E_selected,
                Flux_selected,
                0.1,
                sigma_Cd_selected,
                0.5,
                sigma_CH2_selected,
            )

            # --------------------------------------------------
            # Cd reference
            # --------------------------------------------------
            T_Cd = average_transmission(
                0.1,
                E_selected,
                sigma_Cd_selected,
                Flux_selected,
                atomic_density=4.6e22
            )

            return T_theory, T_polyethylene, T_Cd

        # ------------------------------------------------------
        # Initial calculation
        # ------------------------------------------------------
        result = compute_theoretical_transmission(
            E_min_selected,
            E_max_selected
        )

        T_theory, T_polyethylene, T_Cd = result

        # ------------------------------------------------------
        # Plot theoretical curves
        # ------------------------------------------------------
        theory_line, = ax.plot(
            thicknesses,
            T_theory,
            "o--",
            color="#E69F00",
            markerfacecolor="white",
            markeredgecolor="#E69F00",
            linewidth=1.5,
            label="Beer-Lambert model"
        )

        polyethylene_point, = ax.plot(
            6.0,
            T_polyethylene,
            "o",
            color="#FF00E6",
            markerfacecolor="white",
            markeredgecolor="#FF00E6",
            label="Polyethylene + Cd reference"
        )

        cd_point, = ax.plot(
            1.0,
            T_Cd,
            "o",
            color="#00FF40",
            markerfacecolor="white",
            markeredgecolor="#00FF40",
            label="Cd reference"
        )

        # ======================================================
        # Energy Range Slider
        # ======================================================

        # Leave space at bottom for slider
        fig.subplots_adjust(bottom=0.25)

        slider_ax = fig.add_axes(
            [0.15, 0.09, 0.70, 0.035]
        )

        # Slider works in log10(E)
        log_E_min = np.log10(E_min_data)
        log_E_max = np.log10(E_max_data)

        slider = RangeSlider(
            slider_ax,
            "Energy (eV)",
            log_E_min,
            log_E_max,
            valinit=(
                np.log10(E_min_selected),
                np.log10(E_max_selected)
            ),
            valfmt="%1.2f"
        )

        # ------------------------------------------------------
        # Energy label
        # ------------------------------------------------------
        energy_text = fig.text(
            0.5,
            0.04,
            "",
            ha="center",
            fontsize=10
        )

        def format_energy(E):
            """
            Convert energy in eV to a readable unit.
            """

            if E < 1e-3:
                return f"{E * 1e6:.3g} µeV"

            elif E < 1:
                return f"{E * 1e3:.3g} meV"

            else:
                return f"{E:.3g} eV"

        def update_energy_range(val):

            # ----------------------------------------------
            # Convert slider values back to energy
            # ----------------------------------------------
            E_min_selected = 10 ** val[0]
            E_max_selected = 10 ** val[1]

            # ----------------------------------------------
            # Update displayed energy range
            # ----------------------------------------------
            energy_text.set_text(
                f"Selected energy range: "
                f"{format_energy(E_min_selected)} "
                f"→ "
                f"{format_energy(E_max_selected)}"
            )

            # ----------------------------------------------
            # Recalculate theoretical transmission
            # ----------------------------------------------
            result = compute_theoretical_transmission(
                E_min_selected,
                E_max_selected
            )

            if result is None:
                return

            T_theory_new, T_polyethylene_new, T_Cd_new = result

            # ----------------------------------------------
            # Update plotted data
            # ----------------------------------------------
            theory_line.set_ydata(T_theory_new)

            polyethylene_point.set_ydata(
                [T_polyethylene_new]
            )

            cd_point.set_ydata(
                [T_Cd_new]
            )

            # ----------------------------------------------
            # Redraw
            # ----------------------------------------------
            fig.canvas.draw_idle()

        slider.on_changed(update_energy_range)

        # Store slider on figure so it is not garbage collected
        fig._energy_range_slider = slider
        fig._energy_text = energy_text

        # Initialize text
        update_energy_range(slider.val)


    # ==========================================================
    # Plot formatting
    # ==========================================================

    ax.set_xlabel("B$_4$C thickness (mm)")
    ax.set_ylabel("Thermal neutron transmission")
    ax.set_title("Thermal neutron transmission vs thickness")

    ax.grid(True, linestyle="--", alpha=0.5)

    handles, labels = ax.get_legend_handles_labels()

    if labels:
        ax.legend()

    _integrer_canvas(fig, frame)

    return fig



def plot_transmission_thickness_tof(fichiers, datasets, frame=None):
    """
    Plot neutron transmission as a function of Time-of-Flight.

    T(ToF) = (Flux_sample - BG) / (Flux_reference - BG)

    The first file beginning with:
        tl* -> reference
        bg* -> background

    All other files are considered samples.
    """

    import os
    import numpy as np
    import matplotlib.pyplot as plt

    if frame is not None:
        for widget in frame.winfo_children():
            widget.destroy()

    # ==========================================================
    # Identify reference, background and samples
    # ==========================================================

    ref_file = None
    bg_file = None
    sample_files = []

    for nom in fichiers:

        basename = os.path.basename(nom).lower()

        if basename.startswith("tl"):
            ref_file = nom

        elif basename.startswith("bg"):
            bg_file = nom

        else:
            sample_files.append(nom)

    if ref_file is None:
        raise ValueError(
            "No reference file found. A filename starting with 'tl' is required."
        )

    if bg_file is None:
        raise ValueError(
            "No background file found. A filename starting with 'bg' is required."
        )

    # ==========================================================
    # Background
    # ==========================================================

    bg_data = datasets[bg_file]

    background_level = np.mean(
        bg_data["tof_flux"]["deadtime"]["method1"]["flux"]
    )

    # ==========================================================
    # Reference spectrum
    # ==========================================================

    ref = datasets[ref_file]

    tof_ref = ref["tof_flux"]["deadtime"]["method1"]["ToF"]

    flux_ref = (
        ref["tof_flux"]["deadtime"]["method1"]["flux"]
        - background_level
    )

    unc_ref = ref["tof_flux"]["deadtime"]["method1"]["unc"]

    fig, ax = plt.subplots(figsize=(12, 5))

    # ==========================================================
    # Loop over samples
    # ==========================================================

    for nom in sample_files:

        data = datasets[nom]

        tof = data["tof_flux"]["deadtime"]["method1"]["ToF"]

        flux = (
            data["tof_flux"]["deadtime"]["method1"]["flux"]
            - background_level
        )

        unc = data["tof_flux"]["deadtime"]["method1"]["unc"]

        # ------------------------------------------------------
        # Keep only physically meaningful points
        # ------------------------------------------------------

        mask = (
            (flux > 0)
            & (flux_ref > 0)
            & np.isfinite(flux)
            & np.isfinite(flux_ref)
        )

        transmission = flux[mask] / flux_ref[mask]

        unc_transmission = transmission * np.sqrt(
            (unc[mask] / flux[mask])**2 +
            (unc_ref[mask] / flux_ref[mask])**2
        )

        basename = os.path.basename(nom)

        if basename.lower().startswith("tl"):
            thickness = 0.0
        else:
            try:
                thickness = float(basename.split("mm")[0])
            except ValueError:
                raise ValueError(
                    f"Unable to extract thickness from filename:\n"
                    f"{basename}\n\n"
                    "Expected format:\n"
                    "  tl_reference.dat\n"
                    "  2.5mm_sample.dat\n"
                    "  5mm_sample.dat"
                )

        lignes, caps, bars = ax.errorbar(
            tof[mask] * 1e6,
            transmission,
            yerr=unc_transmission,
            fmt='.-',
            linewidth=1,
            capsize=0,
            label=f"B$_4$C thickness = {thickness:g} mm"
        )

        for bar in bars:
            bar.set_alpha(0.4)

    ax.set_xlabel("Time of Flight (µs)")
    ax.set_ylabel("Transmission")
    ax.set_title("Neutron Transmission vs Time-of-Flight")

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

    plt.tight_layout()

    _integrer_canvas(fig, frame)

    return fig


def plot_total_cross_section(fichiers, frame=None):

    BASE_DIR = Path(__file__).parent

    files = {
        "H":  BASE_DIR / "Shielding" / "set-tot" / "H"  / "sig-tot-H.dat",
        "C":  BASE_DIR / "Shielding" / "set-tot" / "C"  / "sig-tot-C.dat",
        "O":  BASE_DIR / "Shielding" / "set-tot" / "O"  / "sig-tot-O.dat",
        "Si": BASE_DIR / "Shielding" / "set-tot" / "Si" / "sig-tot-Si.dat",
        "Cd": BASE_DIR / "Shielding" / "set-tot" / "Cd" / "sig-tot-Cd.dat",
        "B":  BASE_DIR / "Shielding" / "set-tot" / "B"  / "sig-tot-B.dat",
        "H2": BASE_DIR / "Shielding" / "set-tot" / "H" / "sig-tot-H.txt",
        "O2": BASE_DIR / "Shielding" / "set-tot" / "O" / "sig-tot-O.txt",
    }

    fig, ax = plt.subplots(figsize=(12, 5))

    for name, file in files.items():

        E, sigma = load_cross_section(file)

        ax.plot(
            E,
            sigma,
            linewidth=1.5,
            label=name
        )

    # Polyéthylène CH2
    E_H, sigma_H = load_cross_section(files["H"])
    E_C, sigma_C = load_cross_section(files["C"])

    sigma_C_interp = interp1d(
        E_C,
        sigma_C,
        bounds_error=False,
        fill_value="0.0"
    )(E_H)

    sigma_CH2 = sigma_C_interp + 2 * sigma_H

    ax.plot(
        E_H,
        sigma_CH2,
        "--",
        linewidth=2,
        label="CH₂"
    )

    ax.set_xlabel("Energy (eV)")
    ax.set_ylabel("Total cross section (barns)")
    ax.set_xlim(1e-3, 1e6)

    ax.set_title("Total neutron cross sections")

    ax.grid(True, which="both", alpha=0.3)

    ax.legend()
    _integrer_canvas(fig, frame)

    plt.tight_layout()

    if frame is not None:
        return fig

def plot_transmission_vs_energy(fichiers, datasets, frame=None):

    thickness_aerogel = 0.45  # cm
    thickness_Cd = 0.1        # cm (1 mm)
    thickness_CH2 = 0.5       # cm (5 mm)

    BASE_DIR = Path(__file__).parent

    B_file  = BASE_DIR / "Shielding" / "set-tot" / "B" / "sig-tot-B.dat"
    C_file  = BASE_DIR / "Shielding" / "set-tot" / "C" / "sig-tot-C.dat"
    H_file  = BASE_DIR / "Shielding" / "set-tot" / "H" / "sig-tot-H.dat"
    O_file  = BASE_DIR / "Shielding" / "set-tot" / "O" / "sig-tot-O.txt"
    Si_file = BASE_DIR / "Shielding" / "set-tot" / "Si" / "sig-tot-Si.dat"
    Cd_file = BASE_DIR / "Shielding" / "set-tot" / "Cd" / "sig-tot-Cd.dat"
    
    
    E_mix, sigma_mix, sigma_Cd, sigma_CH2 = build_sigma_mix_from_files(
        B_file,
        C_file,
        H_file,
        O_file,
        Si_file,
        Cd_file,
        0.650218276,
        0.001557414014,
        0.2690997816,
        0.07912452836
    )

    # Aerogel
    T_mix = transmission_vs_energy(
        thickness_aerogel,
        sigma_mix,
        atomic_density=3.18154E21
    )

    T_mix_2 = transmission_vs_energy(
        2.0,
        sigma_mix,
        atomic_density=3.18154E21
    )

    # Cd seul
    T_Cd = transmission_vs_energy(
        thickness_Cd,
        sigma_Cd,
        atomic_density=composition_data["Cd"]["atomic_density"]
    )

    # Cd + CH2
    T_Cd_CH2 = transmission_vs_energy_ref(
        thickness_Cd,
        sigma_Cd,
        thickness_CH2,
        sigma_CH2
    )

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(E_mix, T_mix, label="Aerogel 4.5 mm")
    ax.plot(E_mix, T_mix_2, label="Aerogel 20 mm")
    ax.plot(E_mix, T_Cd, label="Cd 1 mm")
    ax.plot(E_mix, T_Cd_CH2, label="Cd 1 mm + CH₂ 5 mm")

    ax.axvline(
        17,
        color="k",
        linestyle="--",
        alpha=0.5,
        label="17 eV"
    )

    ax.set_xlabel("Energy (eV)")
    ax.set_ylabel("Transmission")
    ax.set_xlim(1e-3, 1e7)
    ax.set_title("Neutron transmission vs energy")

    ax.grid(True, which="both", alpha=0.3)
    ax.legend()

    _integrer_canvas(fig, frame)
    plt.tight_layout()
    
    if frame is not None:
        return fig

def plot_simulated_source(fichiers, datasets, frame=None, **kwargs):
    """
    Plot the simulated neutron source spectrum.
    """

    BASE_DIR = Path(__file__).parent

    ref_file = (
        BASE_DIR
        / "Shielding"
        / "set-tot"
        / "spectrum_avant_chopper.dat"
    )

    E_ref, Flux_ref_simu = load_cross_section(ref_file)

    Flux_ref_simu = Flux_ref_simu

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        E_ref,
        Flux_ref_simu,
        linewidth=1.5,
        label="Simulated source spectrum"
    )

    ax.set_xlabel("Energy (eV)")
    ax.set_ylabel("Flux (arbitrary units)")
    ax.set_title("Simulated neutron source spectrum")

    ax.grid(True, which="both", alpha=0.3)
    ax.legend()

    _integrer_canvas(fig, frame)
    plt.tight_layout()

    if frame is not None:
        return fig