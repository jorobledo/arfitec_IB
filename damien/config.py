
import numpy as np

# Global dictionary of physical parameters modifiable by the GUI
PARAMS = {
    "thickness": 0.8,         # Sample thickness (cm)
    "atom_density": 8.49e22,   # Atomic density (cm^-3)
    "Length": 1.9, 

    "E_min": 3e-3,            # Minimum energy (eV)
    "E_max": 200e-3,          # Maximum energy (eV)
    "t_min": 200e-6,          # Minimum time of flight (s)
    "t_max": 3700e-6,         # Maximum time of flight (s)
    "y_min": 0.0,
    "y_max": 20.0,
}

# Temperature grid for theoretical plots (Maxwellians)
Temp_K = np.arange(260, 400, 5)
N_temp = len(Temp_K)