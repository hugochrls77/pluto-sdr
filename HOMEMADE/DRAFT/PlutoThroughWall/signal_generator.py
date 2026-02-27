import numpy as np

def generate_fmcw_chirp(fs, sweep_time, bandwidth):
    """
    Génère un chirp linéaire (FMCW).
    """
    t = np.arange(0, sweep_time, 1/fs)
    # Fréquence de départ et de fin du balayage
    f0 = -bandwidth / 2
    f1 = bandwidth / 2
    
    # Équation de la phase pour un chirp linéaire
    phase = 2 * np.pi * (f0 * t + (f1 - f0) / (2 * sweep_time) * t**2)
    chirp = np.exp(1j * phase)
    
    # Mise à l'échelle pour le convertisseur (DAC) du PlutoSDR
    return chirp * (2**14)