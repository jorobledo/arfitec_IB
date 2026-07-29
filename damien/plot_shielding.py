import tkinter as tk
from tkinter import ttk
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from physics_NAA import PARAMS, get_R, get_flux, get_lambda, model_tof_epi_NAA
from physics import integrate_thermal_epithermal_flux
from plot import _integrer_canvas
from scipy.interpolate import interp1d

def plot_transmission_concentration(fichiers, datasets, comparison_points=None, frame=None):
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

    THERMAL_T_MIN = 100e-6
    THERMAL_T_MAX = 3700e-6

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
    # Plot
    # ==========================================================

    fig, ax = plt.subplots(figsize=(8,5))

    ax.errorbar(
        concentrations,
        transmissions,
        yerr=unc_transmissions,
        xerr=0.3,
        fmt="o--",
        capsize=4,
        linewidth=1.5,
        markersize=6
    )

    ax.set_xlabel("B$_4$C concentration (%)")
    ax.set_ylabel("Thermal neutron transmission")
    ax.set_title("Thermal neutron transmission")

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

    fig, ax = plt.subplots(figsize=(10, 5))

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

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

    plt.tight_layout()

    _integrer_canvas(fig, frame)

    return fig



def plot_transmission_thickness(fichiers, datasets, comparison_points=None, frame=None):
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

    THERMAL_T_MIN = 100e-6
    THERMAL_T_MAX = 3700e-6

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

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.errorbar(
        thicknesses,
        transmissions,
        yerr=unc_transmissions,
        xerr=0.1,      # modify if needed
        fmt="o--",
        capsize=4,
        linewidth=1.5,
        markersize=6
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

    ax.set_xlabel("B$_4$C thickness (mm)")
    ax.set_ylabel("Thermal neutron transmission")
    ax.set_title("Thermal neutron transmission vs thickness")

    ax.grid(True, linestyle="--", alpha=0.5)
    handles, labels = ax.get_legend_handles_labels()

    if labels:
        ax.legend()

    plt.tight_layout()

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

    fig, ax = plt.subplots(figsize=(10, 5))

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