# HOMEMADE/DRAFT/PlutoSFCW/step1_agility.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time

# Accès au pilote dans READY
sys.path.append(os.path.abspath("../../READY/PlutoDoppler"))
from sdr_device import PlutoDevice

# 1. PARAMÈTRES DU TEST
f_start = 2_100_000_000  # Fréquence de départ (2.1 GHz)
f_step = 10_000_000      # Sauts de 10 MHz
n_steps = 20             # On teste sur 20 sauts pour commencer (200 MHz de BW)

# 2. INITIALISATION
# On utilise ta classe PlutoDevice telle quelle
hw = PlutoDevice(fs=2_000_000, lo=f_start)
hw.set_tx_gain('manual', -40)
hw.set_rx_gain('manual', 30)

# On prépare un signal d'émission fixe (une porteuse pure)
tone = np.ones(1024, dtype=complex) * 0.5

print("--- DÉBUT DU TEST D'AGILITÉ ---")
hw.tx(tone) # Émission en continu

results_amp = []
start_time = time.time()

try:
    for i in range(n_steps):
        target_f = f_start + (i * f_step)
        
        # On utilise ta méthode set_lo
        hw.set_lo(target_f)
        
        # Temps de stabilisation (crucial pour le synthétiseur du Pluto)
        time.sleep(0.01) 
        
        # Capture et mesure de l'amplitude moyenne
        rx = hw.rx()
        amp = np.mean(np.abs(rx))
        results_amp.append(amp)
        
        print(f"Étape {i+1}/{n_steps} : {target_f/1e9:.3f} GHz OK")

finally:
    hw.stop_tx()

total_duration = time.time() - start_time
print(f"--- TEST TERMINÉ ---")
print(f"Temps total pour {n_steps} sauts : {total_duration:.2f} secondes")

# 3. VISUALISATION INSTRUMENTÉE
plt.style.use('dark_background')
plt.figure(figsize=(10, 5))
plt.plot(np.arange(n_steps), results_amp, color='cyan', marker='o', linestyle='--')
plt.title("TEST D'AGILITÉ SFCW : STABILITÉ DE L'AMPLITUDE", color='orange')
plt.xlabel("Numéro du saut (Fréquence croissante)", fontsize=10)
plt.ylabel("Amplitude moyenne reçue", fontsize=10)
plt.grid(True, alpha=0.3)
plt.show()