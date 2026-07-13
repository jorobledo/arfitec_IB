import numpy as np

# Nuclear, physical and experimental constants for Mn-55/Mn-56
PARAMS = {
    "N_A": 6.02214076e23, # Avogadro constant (mol^-1)
    'm': 0.0,             # Mass of the sample (g)
    "M": 54.938,          # Molar mass of Manganese (g/mol)
    "t_half": 2.5785,     # Radioactive half-life of Mn-56 (hours)
    "y": 0.989,           # Gamma emission intensity / yield (846.77 keV)
    "C": 1.0,             # Concentration of element in target
    "eps": 1.0,           # Detector efficiency for this energy
    "eta": 1.0,           # Isotopic abundance of Mn-55
    "F_Cd": 1.0,          # Cadmium correction factor
    "G_th": 0.984,        # Thermal self-shielding factor
    "G_epi": 0.744,       # Epithermal self-shielding factor
    "sig_th": 13.3e-24,   # Fictitious thermal cross section (cm^2)
    "sig_epi": 14.0e-24   # Epithermal cross section / Resonance integral (cm^2)
}

def get_lambda():
    """Calculates the decay constant (s^-1) from t_half."""
    return np.log(2) / (PARAMS["t_half"] * 3600)

def get_R(counts, t_i, t_d, t_m):
    """
    Calculates the reaction rate R (s^-1).
    counts: net counts, t_x: irradiation/decay/measurement times (s)
    """
    lmbda = get_lambda()
    
    num = counts * PARAMS["M"] * lmbda
    den = (PARAMS["C"] * PARAMS["y"] * PARAMS["eps"] * PARAMS["eta"] * PARAMS["m"] * PARAMS["N_A"] * 
           (1 - np.exp(-lmbda * t_i)) * 
           np.exp(-lmbda * t_d) * 
           (1 - np.exp(-lmbda * t_m)))
    
    return num / den

def get_flux(R, R_Cd):
    """
    Calculates phi_th (thermal flux) and phi_epi (epithermal flux).
    R: rate without Cadmium protection, R_Cd: rate with Cadmium protection
    """
    R_epi = PARAMS["F_Cd"] * R_Cd # Corrected epithermal activation rate
    
    phi_epi = R_epi / (PARAMS["G_epi"] * PARAMS["sig_epi"])
    phi_th = (R - R_epi) / (PARAMS["G_th"] * PARAMS["sig_th"])
    
    return phi_th, phi_epi