import numpy as np
from scipy.interpolate import interp1d

# ------------------------------------------------------
# Composition data
# ------------------------------------------------------

composition_data = {
    5.0: {
        "fract_mol": (
            0.2269124769,
            0.0001784510163,
            0.03083388815,
            0.009066216415
        ),
        "atomic_density": 1.54674E+21
    },

    10.0: {
        "fract_mol": (
            0.3825795835,
            0.002749083623,
            0.4750039463,
            0.1396673866
        ),
        "atomic_density": 2.09464E+21
    },

    20.0: {
        "fract_mol": (
            0.5823229657,
            0.00015027454,
            0.02596537949,
            0.00763470856
        ),
        "atomic_density": 3.01085E+21
    },

    25.0: {
        "fract_mol": (
            0.650218276,
            0.001557414014,
            0.2690997816,
            0.07912452836
        ),
        "atomic_density": 3.54494e21
    }
}


# ==========================================================
# Cross section loading
# ==========================================================

def load_cross_section(filename):

    data = np.loadtxt(
        filename,
        usecols=(0, 1)
    )

    E = data[:, 0]
    sigma = data[:, 1]

    return E, sigma


# ==========================================================
# Microscopic mixture cross section
# ==========================================================

def compute_sigma_mix(
    sigma_B,
    sigma_C,
    sigma_H,
    sigma_O,
    sigma_Si,
    f_B4C,
    f_PDMS,
    f_SiO2,
    f_MTMS
):
    # sections efficaces des composés

    sigma_B4C = (
        4*sigma_B
        + sigma_C
    )

    sigma_PDMS = 700 * (
        2*sigma_C
        + 6*sigma_H
        + sigma_Si
        + sigma_O
    )

    sigma_SiO2 = (
        sigma_Si
        + 2*sigma_O
    )

    sigma_MTMS = (
        4*sigma_C
        + 12*sigma_H
        + sigma_Si
        + 3*sigma_O
    )

    # fractions molaires (25%)

    f_B4C  = 0.650218276
    f_PDMS = 0.001557414014
    f_SiO2 = 0.2690997816
    f_MTMS = 0.07912452836

    sigma_mix = (
        f_B4C  * sigma_B4C
        + f_PDMS * sigma_PDMS
        + f_SiO2 * sigma_SiO2
        + f_MTMS * sigma_MTMS
    )

    return sigma_mix


# ==========================================================
# Build mixture from files
# ==========================================================

def build_sigma_mix_from_files(
    file_B,
    file_C,
    file_H,
    file_O,
    file_Si,
    f_B4C,
    f_PDMS,
    f_SiO2,
    f_MTMS
):
    E_H, sigma_H = load_cross_section(file_H)

    E_B, sigma_B = load_cross_section(file_B)
    E_C, sigma_C = load_cross_section(file_C)
    E_O, sigma_O = load_cross_section(file_O)
    E_Si, sigma_Si = load_cross_section(file_Si)

    E_common = E_H

    sigma_C = interp1d(
        E_C,
        sigma_C,
        bounds_error=False,
        fill_value="extrapolate"
    )(E_common)

    sigma_B = interp1d(
        E_B,
        sigma_B,
        bounds_error=False,
        fill_value="extrapolate"
    )(E_common)

    sigma_O = interp1d(
        E_O,
        sigma_O,
        bounds_error=False,
        fill_value="extrapolate"
    )(E_common)

    sigma_Si = interp1d(
        E_Si,
        sigma_Si,
        bounds_error=False,
        fill_value="extrapolate"
    )(E_common)

    sigma_mix = compute_sigma_mix(
        sigma_B,
        sigma_C,
        sigma_H,
        sigma_O,
        sigma_Si,
        f_B4C,
        f_PDMS,
        f_SiO2,
        f_MTMS
    )

    return E_common, sigma_mix


# ==========================================================
# Energy-dependent transmission
# ==========================================================

def transmission_vs_energy(
    thickness_cm,
    sigma_mix,
    atomic_density=3.54494e19
):

    Sigma_macro = atomic_density * sigma_mix * 1e-24

    return np.exp(
        -Sigma_macro * thickness_cm
    )


# ==========================================================
# Spectrum-averaged transmission
# ==========================================================

def average_transmission(
    thickness_cm,
    E,
    sigma_mix,
    flux_incident,
    atomic_density=3.54494e19
):

    T_E = transmission_vs_energy(
        thickness_cm,
        sigma_mix,
        atomic_density
    )

    transmitted_flux = flux_incident * T_E

    return (
        np.trapezoid(transmitted_flux, E)
        /
        np.trapezoid(flux_incident, E)
    )