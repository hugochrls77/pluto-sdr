# HOMEMADE/DRAFT/PlutoSFCW/step4_sfcw_calibration.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time

sys.path.append(os.path.abspath("../../READY/PlutoDoppler"))
from sdr_device import PlutoDevice

# CONFIGURATION (Identique pour cohérence)
f_start, f_step, n_steps = 2_100_000_000, 5_000_000, 100
bw_total = f_step * n_steps
res_dist = 299792458 / (2 * bw_total)
dist_axis = np.arange(n_steps) * res_dist

hw = PlutoDevice(fs=2_000_000, lo=f_start)
hw.set_tx_gain('manual', -40)
hw.set_rx_gain('manual', 35)

def get_scan():
    complex_data = []
    hw.tx(np.ones(1024, dtype=complex) * 0.5)
    for i in range(n_steps):
        hw.set_lo(f_start + (i * f_step))
        time.sleep(0.005) # Stabilisation du LO
        complex_data.append(np.mean(hw.rx()))
    hw.stop_tx()
    return np.array(complex_data)

# 1. ÉTAPE DE CALIBRATION (La pièce doit être vide)
input("Écartez-vous du radar et appuyez sur Entrée pour calibrer...")
ref_data = get_scan()
print("Calibration effectuée.")

# 2. ÉTAPE DE DÉTECTION
input("Placez-vous devant le radar et appuyez sur Entrée pour scanner...")
live_data = get_scan()

# 3. TRAITEMENT DIFFÉRENTIEL (On soustrait les vecteurs complexes)
# Cela annule le pic de 11.69m et tout le décor fixe
diff_data = live_data - ref_data
range_profile = np.fft.ifft(diff_data * np.hanning(n_steps))
range_db = 20 * np.log10(np.abs(range_profile) + 1e-12)

# 4. VISUALISATION
plt.style.use('dark_background')
plt.figure(figsize=(12, 6))
plt.plot(dist_axis, range_db, color='#ff0055', lw=2)
plt.title("SFCW - DÉTECTION APRÈS SOUSTRACTION DU DÉCOR", color='cyan')
plt.xlabel("Distance (mètres)")
plt.ylabel("Puissance (dB)")
plt.xlim(0, 20) # On regarde les 10 premiers mètres
plt.grid(True, alpha=0.2)
plt.show()