# HOMEMADE/DRAFT/PlutoSFCW/step3_range_profile.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time

sys.path.append(os.path.abspath("../../READY/PlutoDoppler"))
from sdr_device import PlutoDevice

# 1. CONFIGURATION (Identique au test précédent)
f_start, f_step, n_steps = 2_100_000_000, 5_000_000, 100
bw_total = f_step * n_steps # 500 MHz

hw = PlutoDevice(fs=2_000_000, lo=f_start)
hw.set_tx_gain('manual', -45)
hw.set_rx_gain('manual', 35)

tone = np.ones(1024, dtype=complex) * 0.5
hw.tx(tone)

complex_data = []

print(f"Acquisition SFCW ({bw_total/1e6} MHz de bande)...")
for i in range(n_steps):
    hw.set_lo(f_start + (i * f_step))
    time.sleep(0.005)
    complex_data.append(np.mean(hw.rx()))

hw.stop_tx()
complex_data = np.array(complex_data)

# --- LE COEUR DU RADAR SFCW : IFFT ---
# On applique une fenêtre de Hanning pour éviter que le pic de 0m n'écrase tout
window = np.hanning(n_steps)
# L'IFFT transforme les variations de phase en pics de distance
range_profile = np.fft.ifft(complex_data * window)
range_db = 20 * np.log10(np.abs(range_profile) + 1e-12)

# Calcul de l'axe X (Distance)
# Résolution = c / (2 * BW_total)
res_dist = 299792458 / (2 * bw_total)
dist_axis = np.arange(n_steps) * res_dist

# --- VISUALISATION ---
plt.style.use('dark_background')
plt.figure(figsize=(12, 6))
plt.plot(dist_axis, range_db, color='#00ff41', lw=2, marker='.', markersize=4)

plt.title(f"PROFIL DE DISTANCE SFCW - Résolution: {res_dist*100:.1f} cm", color='cyan')
plt.xlabel("Distance (mètres)", fontsize=10)
plt.ylabel("Puissance reçue (dB)", fontsize=10)
plt.xlim(0, 20) # On regarde les 10 premiers mètres
plt.grid(True, alpha=0.2, linestyle='--')

# Marqueur pour le pic principal
max_idx = np.argmax(range_db[1:]) + 1 # On ignore le point 0 (leakage)
plt.axvline(dist_axis[max_idx], color='red', linestyle='--', alpha=0.5, 
            label=f"Echo principal: {dist_axis[max_idx]:.2f} m")
plt.legend()

plt.show()