# HOMEMADE/DRAFT/PlutoFMCW/step2_sync.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os

# Accès aux modules de base
sys.path.append(os.path.abspath("../../PlutoDoppler"))
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator

# 1. Configuration instrumentée
fs, fc, n_samples, bw = 2_000_000, 2_100_000_000, 4096, 20_000_000

# 2. Acquisition (Câble SMA toujours branché)
hw = PlutoDevice(fs=fs, lo=fc)
hw.sdr.rx_buffer_size = n_samples * 4
hw.sdr.tx_hardwaregain_chan0 = -30
hw.set_rx_gain('manual', 30)

chirp_tx = SignalGenerator.generate_chirp(fs, n_samples, bw)
hw.tx(chirp_tx)
rx_data = hw.rx()
hw.stop_tx()

# 3. CALCUL DE LA SYNCHRONISATION (Corrélation)
# On cherche où le RX ressemble le plus au TX
correlation = np.abs(np.correlate(rx_data, chirp_tx, mode='valid'))
offset_samples = np.argmax(correlation)
offset_ms = (offset_samples / fs) * 1000

# 4. ALIGNEMENT
rx_aligned = rx_data[offset_samples : offset_samples + n_samples]

# 5. VISUALISATION INSTRUMENTÉE
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Graphe 1 : Le "radar" de synchronisation
t_corr = np.arange(len(correlation)) / fs * 1000
ax1.plot(t_corr, correlation, color='#00ff41', label="Niveau de Corrélation (Force de ressemblance)")
ax1.axvline(offset_ms, color='red', linestyle='--', label=f"Départ détecté à : {offset_ms:.3f} ms")
ax1.set_title("PHASE 2 : RECHERCHE DU DÉCALAGE (TRIGGER)", color='cyan', fontsize=12)
ax1.set_xlabel("Décalage temporel testé (ms)", fontsize=10)
ax1.set_ylabel("Amplitude de corrélation", fontsize=10)
ax1.grid(True, alpha=0.3, linestyle=':')
ax1.legend()

# Graphe 2 : Vérification de la superposition
t_aligned = np.arange(n_samples) / fs * 1000
ax2.plot(t_aligned, np.real(rx_aligned), color='#ff9900', label="Signal RX (Recalé)")
ax2.plot(t_aligned, np.real(chirp_tx), color='#00d4ff', alpha=0.5, label="Signal TX (Référence)")
ax2.set_title("VÉRIFICATION DE L'ALIGNEMENT", color='orange', fontsize=12)
ax2.set_xlabel("Temps relatif au début du Chirp (ms)", fontsize=10)
ax2.set_ylabel("Amplitude", fontsize=10)
ax2.grid(True, alpha=0.3, linestyle=':')
ax2.legend()

plt.tight_layout()
plt.show()