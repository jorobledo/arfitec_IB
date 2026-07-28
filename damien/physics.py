import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad
import scipy.constants as cst
import os
from scipy.optimize import curve_fit
from config import PARAMS
    
""" Constants """

Na = cst.Avogadro 
R_gaz = cst.R
Temp = 293
k_b = cst.Boltzmann
masse_n = 1.67492750056 * 10**(-27)
R_tube = 1.25
angle = 0 * np.pi / 180
atom_dens = 10**6 * Na / (R_gaz * Temp) / 1e6
eV = 1.602176634e-19
ED = 11e-6

t_min = PARAMS['t_min']
t_max = PARAMS['t_max']
E_min = PARAMS['E_min']
E_max = PARAMS['E_max']


def load_metadata(fichier):
    """Extract header parameters from data file."""
    props = {}
    with open(fichier, "r") as f:
        for ligne in f:
            if "Dead time" in ligne: props['dead_time'] = float(ligne.split(":")[1])
            if "Channel width" in ligne: props['channel_width'] = float(ligne.split(":")[1])
            if "Number of frames" in ligne: props['nbr_frames'] = float(ligne.split(":")[1])
            if "Path length" in ligne: props['path_length'] = float(ligne.split(":")[1]) * 1e-2
    return props


def apply_dead_time_correction(counts, dead_time, nbr_frames, channel_width):
    """Corrects counting deficit due to detector dead time."""
    return counts / (1 - counts * dead_time / (nbr_frames * channel_width))


def remove_background(counts, n_pts=100):
    """Calculates and subtracts average background measured on last channels."""
    bg = np.mean(counts[-n_pts:])
    return counts - bg


def apply_grouping_methode1(flux, M=20):
    """Smoothing by moving average (Method 1)."""
    window = np.ones(M) / M
    return np.convolve(flux, window, mode='same')


def apply_grouping_methode2(data, N=10):
    """Grouping by fixed packets (Method 2)."""
    n_ptn = (len(data) // N) * N
    return np.mean(data[:n_ptn].reshape(-1, N), axis=1)


def compute_efficiency_tof(ToF, path_length):
    """Calculates detector efficiency vector as a function of ToF."""
    def integrand(x, t):
        sigma = 848.24 * t / path_length * np.sqrt(2 * 1.6e-19 / masse_n) * 1e-24
        return np.exp(- (2 * atom_dens * sigma / np.cos(angle)) * np.sqrt(R_tube**2 - x**2))
    
    calcul_eff = lambda t: 1 - quad(integrand, 0, R_tube, args=(t, ))[0] / R_tube
    return np.vectorize(calcul_eff)(ToF)


def compute_efficiency_energy(E):
    def integrand(x, e):
        sigma = 848.24 / np.sqrt(e) * 1e-24
        return np.exp(- (2 * atom_dens * sigma / np.cos(angle)) * np.sqrt(R_tube**2 - x**2))
    calcul_eff = lambda e: 1 - quad(integrand, 0, R_tube, args=(e, ))[0] / R_tube
    return np.vectorize(calcul_eff)(E)


def convert_to_energy_scale(flux_tof, ToF, path_length, unc_tof):
    """Transforms temporal flux to energy flux via Jacobian."""
    E = 0.5 * masse_n * (path_length / ToF)**2 / eV
    E_joules = E * eV
    
    # Calculate Jacobian |dt/dE|
    jacobian = 0.5 * path_length * np.sqrt(masse_n / (2 * E_joules**3))
    
    flux_E = flux_tof * jacobian
    flux_E2 = flux_E * E
    unc_E2 = np.abs(unc_tof * (flux_tof / 2.0))
    unc_E = np.abs(unc_E2 / E)
    return E, flux_E, flux_E2, unc_E, unc_E2


def read_reference_file(fichier_ref, E_min, E_max):
    """Reads reference file and returns useful arrays for plotting/comparison.
    Returns: (base_filename, E_ref, sigma_ref, unc_ref, mask_ref, E_plot)
    """
    try:
        chemin_complet_ref = os.path.join("data", fichier_ref)
        donnees_ref = np.loadtxt(chemin_complet_ref)

        if donnees_ref.ndim == 1:
            donnees_ref = np.atleast_2d(donnees_ref)

        num_colonnes = donnees_ref.shape[1]

        if num_colonnes == 2:
            E_ref = donnees_ref[:, 0]
            sigma_ref = donnees_ref[:, 1]
            unc_ref = None
        elif num_colonnes >= 3:
            E_ref = donnees_ref[:, 0]
            sigma_ref = donnees_ref[:, 1]
            unc_ref = donnees_ref[:, 2]
        else:
            raise ValueError("File must contain at least 2 columns.")

        nom_fichier_base = os.path.basename(fichier_ref)
        if nom_fichier_base == "Cu_txs_ncrystal.dat":
            sigma_ref = sigma_ref + 3.78 * np.sqrt(0.025 / E_ref)
            mask_ref = (E_ref >= E_min) & (E_ref <= E_max)
            E_plot = E_ref[mask_ref]
        elif nom_fichier_base == "sigtot-zafiro-FCantargi.dat":
            mask_ref = (E_ref >= E_min) & (E_ref <= E_max)
            E_plot = E_ref[mask_ref]    
        else:
            mask_ref = (E_ref * 1e-3 >= E_min) & (E_ref * 1e-3 <= E_max)
            E_plot = E_ref[mask_ref] * 1e-3

        return nom_fichier_base, E_ref, sigma_ref, unc_ref, mask_ref, E_plot
    except Exception as e:
        raise


def compute_cross_section_uncertainty(flux0, unc0, sample, unc_sample, thickness, atom_density):
    """Propagates uncertainty from ToF ratio to cross section."""
    with np.errstate(divide='ignore', invalid='ignore'):
        Tr = sample / flux0
        dTr = np.sqrt((unc_sample / flux0)**2 + (sample * unc0 / flux0**2)**2)
        unc_sigma = np.abs(1.0 / (atom_density * thickness) * dTr / Tr * 1e24)
    unc_sigma = np.where(np.isfinite(unc_sigma), unc_sigma, 0.0)
    return unc_sigma


def compute_amp_init_from_ref(sigma_ref, mask_amp_ref, cross_sec_m1_raw, mask_E0):
    """Calculates initial amplitude factor from reference if present."""
    try:
        num = np.mean(sigma_ref[mask_amp_ref])
        den = np.mean(cross_sec_m1_raw[mask_E0])
        if den == 0 or not np.isfinite(den):
            return 1.0
        return float(num / den)
    except Exception:
        return 1.0


def compute_grouping_cross_section_m2(ToF_canal, flux0_tof, sample_tof, unc0_tof, uncS_tof, path_length, N_actuel, thickness, atom_density, E_min, E_max):
    """Applies grouping method 2 and returns (ToF_g, E_g, cross_sec_g, unc_g, mask_g)."""
    ToF_g = apply_grouping_methode2(ToF_canal, N=N_actuel)
    flux0_g = apply_grouping_methode2(flux0_tof, N=N_actuel)
    sample_g = apply_grouping_methode2(sample_tof, N=N_actuel)

    unc0_g = np.sqrt(np.abs(apply_grouping_methode2(unc0_tof**2, N=N_actuel) / N_actuel))
    uncS_g = np.sqrt(np.abs(apply_grouping_methode2(uncS_tof**2, N=N_actuel) / N_actuel))

    E_g = 0.5 * masse_n * (path_length / ToF_g)**2 / eV

    with np.errstate(divide='ignore', invalid='ignore'):
        Tr_g = sample_g / flux0_g
        cross_sec_g = cross_section(Tr_g, thickness, atom_density)

    cross_sec_g = np.clip(cross_sec_g, 0, None)
    unc_g = compute_cross_section_uncertainty(flux0_g, unc0_g, sample_g, uncS_g, thickness, atom_density)
    mask_g = (E_g >= E_min) & (E_g <= E_max)
    return ToF_g, E_g, cross_sec_g, unc_g, mask_g


def compute_fit_results_from_dataset(data):
    """Calculates fits and models ToF/E needed for plots 7.x.
    Returns a dict with parameters, models and metrics (R², T, masks...).
    """
    fit_results = {}
    t_min = PARAMS['t_min']
    t_max = PARAMS['t_max']

    p0_pure = [1e-15, 620000.0]

    popt_1, pcov_1 = curve_fit(maxwell_model_tof, data['ToF'], data['flux_tof'], p0=p0_pure)
    a0_tof_pure_1, a1_tof_pure_1 = popt_1[0], popt_1[1]
    perr_1 = np.sqrt(np.diag(pcov_1))

    mask_1 = (data['ToF'] >= t_min) & (data['ToF'] <= t_max)
    flux_modele_1 = maxwell_model_tof(data['ToF'], a0_tof_pure_1, a1_tof_pure_1)
    r_squared_1 = calculate_r_squared(data['flux_tof'][mask_1], flux_modele_1[mask_1])

    popt_2, pcov_2 = curve_fit(maxwell_model_tof, data['ToF_grouped'], data['flux_tof_grouped'], p0=p0_pure)
    a0_tof_pure_2, a1_tof_pure_2 = popt_2[0], popt_2[1]
    perr_2 = np.sqrt(np.diag(pcov_2))

    mask_2 = (data['ToF_grouped'] >= t_min) & (data['ToF_grouped'] <= t_max)
    flux_modele_2 = maxwell_model_tof(data['ToF_grouped'], a0_tof_pure_2, a1_tof_pure_2)
    r_squared_2 = calculate_r_squared(data['flux_tof_grouped'][mask_2], flux_modele_2[mask_2])

    T_1 = (masse_n * data['meta']['path_length']**2) / (2 * k_b * a1_tof_pure_1 * 1e-12)
    T_2 = (masse_n * data['meta']['path_length']**2) / (2 * k_b * a1_tof_pure_2 * 1e-12)

    borne_inf_tof_epi = [0.0, 1e5, 0.0, 0.01, 0.0, 0.01]
    borne_sup_tof_epi = [np.inf, 1e7, np.inf, 5.0, 2.0, 20.0]

    p0_t_epi = [
        np.max(data['flux_tof']) * (data['ToF'][np.argmax(data['flux_tof'])] * 1e6)**5,
        620000.0,
        np.mean(data['flux_tof'][-50:]),
        0.5,
        0.27,
        0.921
    ]

    model_fit_lambda = lambda t, a0, a1, a2, Ed, b, beta: model_tof_epi(t, a0, a1, a2, Ed, b, beta, data['E'])

    popt_epi, pcov_epi = curve_fit(model_fit_lambda, data['ToF'], data['flux_tof'], p0=p0_t_epi, bounds=(borne_inf_tof_epi, borne_sup_tof_epi))

    a0_epi_1, a1_epi_1, a2_epi_1, Ed_epi_1, b_epi_1, beta_epi_1 = popt_epi
    perr_epi_1 = np.sqrt(np.diag(pcov_epi))

    flux_modele_1_epi = model_tof_epi(data['ToF'], a0_epi_1, a1_epi_1, a2_epi_1, Ed_epi_1, b_epi_1, beta_epi_1, data['E'])
    r_squared_1_epi = calculate_r_squared(data['flux_tof'][mask_1], flux_modele_1_epi[mask_1])

    T_1_epi = (masse_n * data['meta']['path_length']**2) / (2 * k_b * a1_epi_1 * 1e-12)

    flux_epi_pure = model_epi_pure(data['ToF'], 5.5710*1e31, 3.2099*1e10, -12.973, 425506) / 10
    flux_luis = flux_modele_1 + flux_epi_pure

    fit_results.update({
        'a0_tof_pure_1': a0_tof_pure_1, 'a1_tof_pure_1': a1_tof_pure_1,
        'a0_tof_pure_2': a0_tof_pure_2, 'a1_tof_pure_2': a1_tof_pure_2,
        'a0_epi_1': a0_epi_1, 'a1_epi_1': a1_epi_1, 'a2_epi_1': a2_epi_1,
        'Ed_epi_1': Ed_epi_1, 'T_1_epi': T_1_epi, 'b_epi_1': b_epi_1, 'beta_epi_1': beta_epi_1,
        'flux_modele_1': flux_modele_1, 'flux_modele_2': flux_modele_2,
        'flux_modele_1_epi': flux_modele_1_epi, 'flux_epi_pure': flux_epi_pure, 'flux_luis': flux_luis,
        'mask_1': mask_1, 'mask_2': mask_2,
        'T_1': T_1, 'T_2': T_2,
        'r_squared_1': r_squared_1, 'r_squared_2': r_squared_2, 'r_squared_1_epi': r_squared_1_epi
    })

    return fit_results


def compute_plot8_models(data, fit_results=None):
    """Calculates models and conversions needed for plots 8.x.
    If `fit_results` (temporal) is provided, also converts models ToF -> E.
    Returns a dict with keys: flux_modele_1, flux_modele_2, jacobian, flux_tof_pure_converted, flux_tof_epi_converted, masks, and parameters T, R².
    """
    E_min = PARAMS['E_min']
    E_max = PARAMS['E_max']

    mask_E = (data['E'] >= E_min) & (data['E'] <= E_max)
    mask_epi = (data['E'] >= 0.4) & (data['E'] <= E_max)

    borne_inf = [0.0, 5.8]
    borne_sup = [np.inf, 232.0]

    E_joules_all = data['E'] * eV
    jacobian = 0.5 * data['meta']['path_length'] * np.sqrt(masse_n / (2 * E_joules_all**3))

    p0_1 = [np.max(data['flux_E']) / np.max(data['E']), 1 / (k_b / eV * 300)]
    popt_1, pcov_1 = curve_fit(maxwell_model_E, data['E'][mask_E], data['flux_E'][mask_E], p0=p0_1, bounds=(borne_inf, borne_sup))
    a0_best_1, a1_best_1 = popt_1[0], popt_1[1]
    perr_1 = np.sqrt(np.diag(pcov_1))

    flux_modele_1 = maxwell_model_E(data['E'], a0_best_1, a1_best_1)
    r_squared_1 = calculate_r_squared(data['flux_E'][mask_E], flux_modele_1[mask_E])
    T_1 = 1 / (k_b / eV * a1_best_1)

    p0_2 = [np.max(data['flux_E2']) / np.max(data['E']), 1 / (k_b / eV * 300)]
    popt_2, pcov_2 = curve_fit(maxwell_model_E_corr, data['E'][mask_E], data['flux_E2'][mask_E], p0=p0_2, bounds=(borne_inf, borne_sup))
    a0_best_2, a1_best_2 = popt_2[0], popt_2[1]

    flux_modele_2 = maxwell_model_E_corr(data['E'], a0_best_2, a1_best_2)
    r_squared_2 = calculate_r_squared(data['flux_E2'][mask_E], flux_modele_2[mask_E])
    T_2 = 1 / (k_b / eV * a1_best_2)

    out = {
        'flux_modele_1': flux_modele_1,
        'flux_modele_2': flux_modele_2,
        'jacobian': jacobian,
        'mask_E': mask_E,
        'mask_epi': mask_epi,
        'T_1': T_1,
        'T_2': T_2,
        'r_squared_1': r_squared_1,
        'r_squared_2': r_squared_2
    }

    # Expose fitted parameters for possible downstream use
    out['a0_best_1'] = a0_best_1
    out['a1_best_1'] = a1_best_1
    out['a0_best_2'] = a0_best_2
    out['a1_best_2'] = a1_best_2

    if fit_results is not None:
        a0_tof = fit_results.get('a0_tof_pure_1')
        a1_tof = fit_results.get('a1_tof_pure_1')
        if a0_tof is not None and a1_tof is not None:
            flux_tof_pure_poly = maxwell_model_tof(data['ToF'], a0_tof, a1_tof)
            flux_tof_pure_converted = flux_tof_pure_poly * jacobian
            out['flux_tof_pure_converted'] = flux_tof_pure_converted

        # If epithermal temporal params exist, convert them too
        try:
            a0_from_tof = fit_results['a0_epi_1']
            a1_from_tof = fit_results['a1_epi_1']
            a2_from_tof = fit_results['a2_epi_1']
            Ed_from_tof = fit_results['Ed_epi_1']
            b_from_tof = fit_results['b_epi_1']
            beta_from_tof = fit_results['beta_epi_1']
            flux_tof_epi_pure = model_tof_epi(data['ToF'], a0_from_tof, a1_from_tof, a2_from_tof, Ed_from_tof, b_from_tof, beta_from_tof, data['E'])
            flux_tof_epi_converted = flux_tof_epi_pure * jacobian
            out['flux_tof_epi_converted'] = flux_tof_epi_converted
        except KeyError:
            pass

    return out

def fit_maxwellian_grid_search(ToF, flux, path_length):
    """Determines the best temperature by least squares (increments of 5K)."""
    Temp_K = np.arange(260, 400, 5)
    LSM = []

    for T in Temp_K:
        maxwellian = 0.5 * (masse_n / (k_b * T))**2 * path_length**4 / ToF**5 * np.exp(-masse_n * path_length**2 / (2 * k_b * T * ToF**2))
        
        fact_amplitude = np.max(flux) / np.max(maxwellian)
        maxwellian_norm = maxwellian * fact_amplitude
        
        # Calculate least squares error (starting from channel 20)
        err_global = np.sum((maxwellian_norm[20:] - flux[20:])**2)
        LSM.append(err_global)
        
    idx_best = np.argmin(LSM)
    return Temp_K[idx_best], LSM[idx_best]

def maxwell_model_tof(t, a0, a1):
    """Pure Maxwellian model in time-of-flight (ToF) domain."""
    return a0 / t**5 * np.exp(-a1 / (t * 1e6)**2)


def model_tof_epi(t, a0, a1, a2, Ed, b, beta, E_array):
    """Global model combining thermal (Maxwell) and epithermal contribution."""
    F_M = (a0 / (t * 1e6)**5) * np.exp(-a1 / (t * 1e6)**2)
    F_E = a2 * (1 - np.exp(-(E_array / Ed)**2)) * E_array**(b - 1) * np.exp(-E_array / beta)
    return F_M + F_E


def calculate_r_squared(y_true, y_pred):
    """Calculate R² coefficient of determination to evaluate fit quality."""
    residus = y_true - y_pred
    ss_res = np.sum(residus**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    return 1 - (ss_res / ss_tot)

def model_epi_pure(t, a2, a3, a4, a5):
    return a2 * (1 - np.exp(-a3 / (1e6 * t)**2)) * (1e6 * t)**a4 * np.exp(-a5 / (1e6 * t)**2)

def maxwell_model_E(E, a0, a1):
    """Standard Maxwellian model in energy domain."""
    return a0 * E * np.exp(-a1 * E)


def maxwell_model_E_corr(E, a0, a1):
    """Corrected Maxwellian model (multiplied by E) in energy domain."""
    return a0 * E**2 * np.exp(-a1 * E)


def maxwell_epi_analytique_E(E, a0, a1, a2, Ed, b_param, beta_param):
    """Global model (Thermal + Epithermal) for flux spectrum in energy Flux(E)."""
    F_M = a0 * E * np.exp(-a1 * E)
    F_E = a2 * (1 - np.exp(-(E / Ed)**2)) * E**(b_param - 1) * np.exp(-E / beta_param)
    return F_M + F_E


def maxwell_epi_analytique_E_corr(E, a0, a1, a2, Ed, b_param, beta_param):
    """Global model (Thermal + Epithermal) for corrected spectrum Flux(E) * E."""
    F_M = a0 * E**2 * np.exp(-a1 * E)
    F_E = a2 * (1 - np.exp(-(E / Ed)**2)) * E**b_param * np.exp(-E / beta_param)
    return F_M + F_E



def transmission_coeff(flux_sample, flux0):
    return (flux_sample / flux0)

def cross_section(Tr, d, n):
    return -1/(n*d)*np.log(Tr)*1e24


def process_neutron_data(fichier):
    """Execute the entire processing pipeline for a given file."""
    # 1. File loading and metadata
    meta = load_metadata(fichier)
    channels, counts = np.loadtxt(fichier, skiprows=15, unpack=True)
    
    # 2. Corrections primaires (Temps mort, bruit de fond)
    counts_dt = apply_dead_time_correction(counts, meta['dead_time'], meta['nbr_frames'], meta['channel_width'])
    counts_bg_corr = remove_background(counts_dt)
    
    therm_counts = remove_background(counts)
    
    # Normalisation par pulses et incertitudes
    flux_normalise = counts_bg_corr / meta['nbr_frames']
    therm_norm_flux = therm_counts / meta['nbr_frames']
    unc_normalisee = np.sqrt(counts) / meta['nbr_frames']
    
    # 3. Calculate time kinetics (ToF)
    ToF = (meta['channel_width'] * channels * 1e-6) - ED
    
    # 4. Smoothing and efficiency correction (Time Domain)
    flux_lisse = apply_grouping_methode1(flux_normalise)
    mean_therm_norm_flux = apply_grouping_methode1(therm_norm_flux)
    eff_ToF = compute_efficiency_tof(ToF, meta['path_length'])
    flux_tof_ungrouped = flux_normalise / eff_ToF
    flux_final_tof = flux_lisse / eff_ToF
    unc_flux_reelle = unc_normalisee / eff_ToF
    
    # 5. Grouping method 2 (Packets of 10)
    flux_grouped = apply_grouping_methode2(flux_normalise)
    channels_grouped = apply_grouping_methode2(channels)
    ToF_grouped = apply_grouping_methode2(ToF)
    unc_grouped = apply_grouping_methode2(unc_normalisee) / np.sqrt(10)
    
    flux_tof_grouped = apply_grouping_methode2(flux_final_tof)
    
    # 6. Change of variable to Energy Domain
    E, flux_E, flux_E2, unc_E, unc_E2= convert_to_energy_scale(flux_final_tof, ToF, meta['path_length'], unc_normalisee)
    eff_E = compute_efficiency_energy(E)
    
    # Clean output dictionary
    return {
        'meta': meta,
        'channels': channels,
        'channels_grouped': channels_grouped,
        'ToF': ToF,
        'ToF_grouped': ToF_grouped,
        'flux_normalise': flux_normalise,
        'flux_lisse': flux_lisse,
        'mean_therm_norm_flux': mean_therm_norm_flux,
        'flux_grouped': flux_grouped,
        'flux_tof_ungrouped':flux_tof_ungrouped,
        'flux_tof': flux_final_tof,
        'flux_tof_grouped': flux_tof_grouped,
        'unc_tof': unc_normalisee,
        'unc_tof_grouped': unc_grouped,
        'unc_flux_reelle':unc_flux_reelle,
        'E': E,
        'eff_E': eff_E,
        'eff_ToF': eff_ToF,
        'flux_E': flux_E,
        'flux_E2': flux_E2,
        'unc_E': unc_E,
        'unc_E2': unc_E2
    }


Temp_K = np.arange(260,400,5)
N_temp = len(Temp_K)
cmap = plt.cm.coolwarm  