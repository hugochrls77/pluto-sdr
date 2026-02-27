# HOMEMADE/DRAFT/PlutoSFCW/step2_vector_scan.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time

sys.path.append(os.path.abspath("../../READY/PlutoDoppler"))
from sdr_device import PlutoDevice

# 1. PARAMÈTRES (On monte à 100 points pour plus de précision)
f_start = 2_100_000_000 
f_step = 5_000_000       # Sauts de 5 MHz
n_steps = 100            # Bande totale = 500 MHz (Résolution ~30cm)

hw = PlutoDevice(fs=2_000_000, lo=f_start)
hw.set_tx_gain('manual', -40)
hw.set_rx_gain('manual', 30)

# On émet un signal pur
tone = np.ones(1024, dtype=complex) * 0.5
hw.tx(tone)

complex_data = []

print("Scan vectoriel en cours...")
for i in range(n_steps):
    freq = f_start + (i * f_step)
    hw.set_lo(freq)
    time.sleep(0.005) # Stabilisation
    
    rx = hw.rx()
    # On stocke la moyenne COMPLEXE (conserve l'Amplitude ET la Phase)
    val = np.mean(rx)
    complex_data.append(val)

hw.stop_tx()
complex_data = np.array(complex_data)

# 2. VISUALISATION INSTRUMENTÉE (Le plan complexe)
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Graphique de la Phase (L'ADN de la distance)
phases = np.angle(complex_data)
ax1.plot(phases, color='yellow', lw=1.5)
ax1.set_title("ÉVOLUTION DE LA PHASE PAR FRÉQUENCE", color='cyan')
ax1.set_xlabel("Numéro du saut", fontsize=10)
ax1.set_ylabel("Phase (Radians)", fontsize=10)
ax1.grid(True, alpha=0.3)

# Graphique Polaire (Le signal qui tourne)
ax2 = fig.add_subplot(1, 2, 2, projection='polar')
ax2.plot(phases, np.abs(complex_data), color='lime', alpha=0.7)
ax2.set_title("PORTRAIT DE PHASE (VECTORIEL)", color='orange', pad=20)

plt.tight_layout()
plt.show()