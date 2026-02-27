# HOMEMADE/DRAFT/PlutoSFCW/step5_sfcw_final_proto.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time

sys.path.append(os.path.abspath("../../READY/PlutoDoppler"))
from sdr_device import PlutoDevice

# --- CONFIGURATION AVANCÉE ---
f_start, f_step, n_steps = 2_100_000_000, 4_000_000, 200 # 200 points pour filtrer le bruit
OFFSET_MATERIEL = 11.69 # Ton retard interne identifié
bw_total = f_step * n_steps

hw = PlutoDevice(fs=2_000_000, lo=f_start)
hw.set_tx_gain('manual', -50) # On baisse encore pour ne pas éblouir le RX
hw.set_rx_gain('manual', 30)

def get_scan():
    complex_data = []
    # On émet une porteuse pure très faible
    hw.tx(np.ones(1024, dtype=complex) * 0.3)
    for i in range(n_steps):
        hw.set_lo(f_start + (i * f_step))
        time.sleep(0.003) # Stabilisation rapide
        complex_data.append(np.mean(hw.rx()))
    hw.stop_tx()
    return np.array(complex_data)

# 1. CALIBRATION (Reste très loin)
input("Éloigne-toi et ne bouge plus... Appuie sur Entrée")
ref_data = get_scan()
print("Décor enregistré.")

# 2. MESURE (Utilise un objet métallique si possible pour le premier test)
input("Place un objet (ou ta main) à 50cm et ne bouge plus... Appuie sur Entrée")
live_data = get_scan()

# 3. TRAITEMENT DIFFÉRENTIEL
# Soustraction vectorielle pour annuler la fuite directe sans blindage
diff_data = live_data - ref_data
# Fenêtrage de Kaiser (très bon pour isoler les petits pics du bruit de fond)
window = np.kaiser(n_steps, 6)
range_profile = np.fft.ifft(diff_data * window, n=n_steps*2) # Interpolation pour plus de finesse
range_db = 20 * np.log10(np.abs(range_profile) + 1e-12)

# Axe recalé
res_dist = 299792458 / (2 * bw_total)
dist_axis = (np.linspace(0, n_steps, n_steps*2) * res_dist) - OFFSET_MATERIEL

# 4. VISUALISATION
plt.style.use('dark_background')
plt.figure(figsize=(12, 6))
plt.plot(dist_axis, range_db, color='#00ff41', lw=1.5)

plt.title(f"SFCW - DÉTECTION HAUTE RÉSOLUTION (BW: {bw_total/1e6} MHz)", color='cyan')
plt.xlabel("Distance réelle recalculée (mètres)")
plt.ylabel("Niveau de détection (dB)")
plt.xlim(-0.2, 5.0) # On zoome sur les 5 premiers mètres
plt.ylim(-110, -50)
plt.grid(True, alpha=0.2)

plt.show()