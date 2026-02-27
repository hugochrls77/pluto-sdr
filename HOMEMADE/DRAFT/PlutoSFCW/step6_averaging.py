# HOMEMADE/DRAFT/PlutoSFCW/step6_sfcw_averaging.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time

sys.path.append(os.path.abspath("../../READY/PlutoDoppler"))
from sdr_device import PlutoDevice

# CONFIGURATION (On pousse à 800 MHz de BW comme ton dernier test)
f_start, f_step, n_steps = 2_100_000_000, 4_000_000, 200 
OFFSET_MATERIEL = 11.69
N_AVERAGE = 5 # On va scanner 5 fois pour chaque mesure

hw = PlutoDevice(fs=2_000_000, lo=f_start)
hw.set_tx_gain('manual', -55) # Gain TRÈS bas pour ne pas saturer
hw.set_rx_gain('manual', 25)

def get_averaged_scan():
    accumulated_data = np.zeros(n_steps, dtype=complex)
    hw.tx(np.ones(1024, dtype=complex) * 0.3)
    
    print(f"Acquisition de {N_AVERAGE} scans...")
    for a in range(N_AVERAGE):
        for i in range(n_steps):
            hw.set_lo(f_start + (i * f_step))
            time.sleep(0.003)
            accumulated_data[i] += np.mean(hw.rx())
        print(f"  Scan {a+1}/{N_AVERAGE} terminé")
        
    hw.stop_tx()
    return accumulated_data / N_AVERAGE

# 1. CALIBRATION (Reste pétrifié loin du radar)
input("CALIBRATION : Reste loin et ne bouge plus du tout... [Entrée]")
ref_data = get_averaged_scan()

# 2. MESURE (Pose un objet métallique stable, n'utilise pas ta main qui tremble)
input("MESURE : Pose un objet MÉTALLIQUE à 50cm et ne bouge plus... [Entrée]")
live_data = get_averaged_scan()

# 3. TRAITEMENT
diff_data = live_data - ref_data
range_profile = np.fft.ifft(diff_data * np.blackman(n_steps), n=n_steps*2)
range_db = 20 * np.log10(np.abs(range_profile) + 1e-12)

dist_axis = (np.linspace(0, n_steps, n_steps*2) * (3e8/(2*f_step*n_steps))) - OFFSET_MATERIEL

# 4. VISU
plt.style.use('dark_background')
plt.figure(figsize=(12, 6))
plt.plot(dist_axis, range_db, color='#00ff41')
plt.title(f"SFCW AVERAGING (N={N_AVERAGE})", color='cyan')
plt.xlim(-0.2, 3.0)
plt.ylim(-110, -50)
plt.grid(True, alpha=0.2)
plt.show()