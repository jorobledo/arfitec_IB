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
        "atomic_density": 2.43331E+21
    },

    10.0: {
        "fract_mol": (
            0.3825795835,
            0.002749083623,
            0.4750039463,
            0.1396673866
        ),
        "atomic_density": 2.78307E+21
    },

    20.0: {
        "fract_mol": (
            0.5823229657,
            0.00015027454,
            0.02596537949,
            0.00763470856
        ),
        "atomic_density": 3.03834E+21
    },

    25.0: {
        "fract_mol": (
            0.650218276,
            0.001557414014,
            0.2690997816,
            0.07912452836
        ),
        "atomic_density": 3.18154E+21
    },

    "Cd": {
        "atomic_density":4.6e22
    },

    "CH2": {
        "atomic_density": 4e22
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

    sigma_PDMS = 1 * (
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
    file_Cd,
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
    E_Cd, sigma_Cd = load_cross_section(file_Cd)

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

    sigma_Cd = interp1d(
        E_Cd,
        sigma_Cd,
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

    sigma_CH2 = 2 * sigma_H + sigma_C

    return E_common, sigma_mix, sigma_Cd, sigma_CH2


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




def transmission_vs_energy_ref(
    thickness_Cd,
    sigma_Cd,
    thicnkness_CH2,
    sigma_CH2,
    atomic_density_Cd= composition_data["Cd"]["atomic_density"],
    atomic_density_CH2= composition_data["CH2"]["atomic_density"]
):
    Sigma_macro_Cd = atomic_density_Cd * sigma_Cd * 1e-24
    Sigma_macro_CH2 = atomic_density_CH2 * sigma_CH2 * 1e-24


    return np.exp(
        -Sigma_macro_Cd * thickness_Cd
        -Sigma_macro_CH2 * thicnkness_CH2
    )


def average_transmission_ref(
    E,
    flux_incident,
    thickness_Cd,
    sigma_Cd,
    thicnkness_CH2,
    sigma_CH2,
    atomic_density_Cd= composition_data["Cd"]["atomic_density"],
    atomic_density_CH2= composition_data["CH2"]["atomic_density"]
):

    T_E = transmission_vs_energy_ref(
        thickness_Cd,
        sigma_Cd,
        thicnkness_CH2,
        sigma_CH2
    )

    transmitted_flux = flux_incident * T_E

    return (
        np.trapezoid(transmitted_flux, E)
        /
        np.trapezoid(flux_incident, E)
    )