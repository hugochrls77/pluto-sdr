import numpy as np
from scipy import signal
from radar_physics import compute_f_beat, compute_phase_diff

def generate_cpi_signal(R, v, params, N=10000):
    f_beat = compute_f_beat(R, params['bw'], params['Tc'])
    phase_diff = compute_phase_diff(v, params['f'], params['Tc'])
    
    # Correction de l'échantillonnage pour correspondre exactement à l'original
    max_time = 20 / f_beat
    fs = N / max_time 
    t = np.linspace(0, max_time, N, endpoint=False)
    
    window = signal.windows.blackman(N)
    
    cpi_data = []
    for m in range(params['M']):
        noise = np.random.normal(0, 0.1, N)
        sig = np.sin(2 * np.pi * f_beat * t + m * phase_diff) + noise
        cpi_data.append(sig * window)
        
    return np.array(cpi_data), t, fs, f_beat, phase_diff