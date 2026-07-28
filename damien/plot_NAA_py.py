import numpy as np
import matplotlib.pyplot as plt

def plot_counts(file_path):
    """
    Plots the experimental count rate as a function of energy.
    file_path: path to .dat file (col 0: energy, col 1: count rate)
    """
    # Load data from the two columns
    data = np.loadtxt(file_path)
    energy = data[:, 0]
    cts_rate = data[:, 1]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.plot(energy, cts_rate, '-', color='tab:red', linewidth=1.5, label='Experimental Data')
    
    # GUI elements in English
    ax.set_xlabel('Energy (eV)')
    ax.set_ylabel('Count Rate (cps)')
    ax.set_title('Experimental Count Rate vs Energy')
    
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='best')
    
    plt.tight_layout()
    plt.show()

def plot_flux(pos, phi_th, phi_epi):
    """
    Plots the thermal and epithermal flux profiles.
    pos: list/array of irradiation positions, phi_th/phi_epi: calculated fluxes
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.plot(pos, phi_th, 'o-', color='tab:blue', label=r'$\phi_{th}$ (thermal)')
    ax.plot(pos, phi_epi, 's-', color='tab:orange', label=r'$\phi_{epi}$ (epithermal)')
    
    ax.set_xlabel('Irradiation Position')
    ax.set_ylabel(r'Flux (n $\cdot$ cm$^{-2}$ $\cdot$ s$^{-1}$)')
    ax.set_title('Neutron Flux Profile (Mn)')
    
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='best')
    
    plt.tight_layout()
    plt.savefig('flux_profile.png', dpi=300)
    plt.show()