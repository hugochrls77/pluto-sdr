import numpy as np
from scipy.constants import c, pi

def get_radar_params():
    """Retourne les paramètres de configuration du radar."""
    params = {
        'f': 76e9,          # Hz
        'Tc': 40e-6,        # chirp time - s
        'bw': 1.6e9,        # bandwidth - Hz
        'M': 256             # chirps in CPI
    }
    params['wavelength'] = c / params['f']
    params['chirp_rate'] = params['bw'] / params['Tc']
    return params

def compute_f_beat(R, bw, Tc):
    """Calcule la fréquence de battement pour une distance R."""
    return (2 * R * bw) / (c * Tc)

def compute_phase_diff(v, f, Tc):
    """Calcule le déphasage induit par la vitesse v."""
    time_from_vel = 2 * (v * Tc) / c
    return 2 * pi * f * time_from_vel

def get_resolutions(params):
    """Calcule les résolutions théoriques du système."""
    res_range = c / (2 * params['bw'])
    max_vel = params['wavelength'] / (4 * params['Tc'])
    res_vel = params['wavelength'] / (2 * params['M'] * params['Tc'])
    return res_range, max_vel, res_vel

def db_to_lin(x):
    """Convertit une puissance en décibels (dB) vers une échelle linéaire."""
    return 10 ** (x / 10)