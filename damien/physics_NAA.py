import numpy as np

# Nuclear, physical and experimental constants for Mn-55/Mn-56
PARAMS = {
    "N_A": 6.02214076e23, # Avogadro constant (mol^-1)
    "m_mn": 0.092,        # Mass of the sample (g)
    "m_mn_cd": 0.084,     # Mass of the sample for the cadmium experiment(g)
    "M": 54.938,          # Molar mass of Manganese (g/mol)
    "t_half": 2.5785,     # Radioactive half-life of Mn-56 (hours)
    "y": 0.989,           # Gamma emission intensity / yield (846.77 keV)
    "C": 0.8,             # Concentration of element in target
    "eps": 1.0e-3,           # Detector efficiency for this energy
    "eta": 1.0,           # Isotopic abundance of Mn-55
    "F_Cd": 1.0,          # Cadmium correction factor
    "G_th": 0.984,        # Thermal self-shielding factor
    "G_epi": 0.744,       # Epithermal self-shielding factor
    "sig_th": 13.3e-24,   # Fictitious thermal cross section (cm^2)
    "sig_epi": 14.0e-24     # Epithermal cross section / Resonance integral (cm^2)
}

def get_lambda(t_half):
    """Calculates the decay constant (s^-1) from t_half."""
    return np.log(2) / (t_half * 3600)

def get_mean_sig_th(sig_th, T0=300, T=300, g=1): #T0 for ref Temp, T for experimental Temp, g for resonance integral correction factor
    mean_sig_th = sig_th * np.sqrt(np.pi) / 2 * np.sqrt (T0/T) * g
    return mean_sig_th

def get_R(counts, t_i, t_d, t_m, m):
    """
    Calculates the reaction rate R (s^-1).
    counts: net counts, t_x: irradiation/decay/measurement times (s)
    """
    lmbda = get_lambda(PARAMS["t_half"])
    
    num = counts * PARAMS["M"] * lmbda
    den = (PARAMS["C"] * PARAMS["y"] * PARAMS["eps"] * PARAMS["eta"] * m * PARAMS["N_A"] * 
           (1 - np.exp(-lmbda * t_i)) * 
           np.exp(-lmbda * t_d) * 
           (1 - np.exp(-lmbda * t_m)))
    
    return num / den

def get_flux(R, R_Cd):
    """
    Calculates phi_th (thermal flux) and phi_epi (epithermal flux).
    R: rate without Cadmium protection, R_Cd: rate with Cadmium protection
    """
    mean_sig_th = get_mean_sig_th(PARAMS["sig_th"])

    R_epi = PARAMS["F_Cd"] * R_Cd # Corrected epithermal activation rate
    
    phi_epi = R_epi / (PARAMS["G_epi"] * PARAMS["sig_epi"])
    phi_th = (R - R_epi) / (PARAMS["G_th"] * mean_sig_th)
    
    return phi_th, phi_epi

def model_tof_epi_NAA(t, a0, a1, a2, Ed, b, beta, E_array, flux_th, flux_epi):
    """Global model combining thermal (Maxwell) and epithermal contribution."""
    F_M = (a0 / (t * 1e6)**5) * np.exp(-a1 / (t * 1e6)**2)
    F_E = a2 * (1 - np.exp(-(E_array / Ed)**2)) * E_array**(b - 1) * np.exp(-E_array / beta)
    return flux_th * F_M + flux_epi * F_E

# print (get_flux(get_R(), get_R()))  # Example usage of get_flux function