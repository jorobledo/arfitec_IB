import numpy as np

# Constantes nucléaires, physiques et expérimentales pour le Mn-55/Mn-56
PARAMS = {
    "N_A": 6.02214076e23, # Constante d'Avogadro (mol^-1)
    'm': 0.0,             # Masse de l'échantillon (g)
    "M": 54.938,          # Masse molaire du Manganèse (g/mol)
    "t_half": 2.5785,     # Période radioactive du Mn-56 (heures)
    "y": 0.989,           # Intensité d'émission gamma / yield (846.77 keV)
    "C": 1.0,             # Concentration de l'élément dans la cible
    "eps": 1.0,           # Efficacité du détecteur pour cette énergie
    "eta": 1.0,           # Abondance isotopique du Mn-55
    "F_Cd": 1.0,          # Facteur de correction du Cadmium
    "G_th": 0.984,        # Facteur d'auto-protection thermique
    "G_epi": 0.744,       # Facteur d'auto-protection épithermique
    "sig_th": 13.3e-24,   # Section efficace thermique fictive (cm^2)
    "sig_epi": 14.0e-24   # Section efficace épithermique / Intégrale de résonance (cm^2)
}

def get_lambda():
    """Calcule la constante de déchéance (s^-1) à partir de t_half."""
    return np.log(2) / (PARAMS["t_half"] * 3600)

def get_R(counts, t_i, t_d, t_m):
    """
    Calcule le taux de réaction R (s^-1).
    counts: comptes nets, t_x: temps d'irradiation/décroissance/mesure (s)
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
    Calcule phi_th (flux thermique) et phi_epi (flux épithermique).
    R: taux sans protection Cadmium, R_Cd: taux avec protection Cadmium
    """
    R_epi = PARAMS["F_Cd"] * R_Cd # Taux d'activation épithermique corrigé
    
    phi_epi = R_epi / (PARAMS["G_epi"] * PARAMS["sig_epi"])
    phi_th = (R - R_epi) / (PARAMS["G_th"] * PARAMS["sig_th"])
    
    return phi_th, phi_epi