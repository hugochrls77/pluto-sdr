import numpy as np
from scipy import signal
from radar_physics import compute_f_beat, compute_phase_diff, db_to_lin

def generate_multi_target_cpi(targets, params, N=10000, noise_std=0.95):
    """Génère le signal de battement CPI pour de multiples cibles."""
    
    # On garde la même base de temps que précédemment (basée sur une cible à 20m) 
    # pour garantir que fs et max_time restent cohérents avec tes paramètres.
    f_beat_ref = compute_f_beat(20, params['bw'], params['Tc'])
    max_time = 20 / f_beat_ref
    fs = N / max_time 
    t = np.linspace(0, max_time, N, endpoint=False)
    
    window = signal.windows.blackman(N)
    cpi_data = []
    
    for m in range(params['M']):
        # Construction du signal pour chaque cible
        target_signals = []
        for r, v, p in targets:
            f_b = compute_f_beat(r, params['bw'], params['Tc'])
            phi_diff = compute_phase_diff(v, params['f'], params['Tc'])
            # Signal d'une cible avec son atténuation
            sig = np.sin(2 * np.pi * f_b * t + m * phi_diff) * db_to_lin(p)
            target_signals.append(sig)
            
        # Bruit thermique du récepteur
        noise = np.random.normal(0, noise_std, N)
        
        # Somme des signaux de toutes les cibles + bruit
        total_sig = np.sum(target_signals, axis=0) + noise
        cpi_data.append(total_sig * window)
        
    return np.array(cpi_data), t, fs