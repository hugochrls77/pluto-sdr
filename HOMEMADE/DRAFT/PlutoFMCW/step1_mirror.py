# HOMEMADE/DRAFT/PlutoFMCW/step1_mirror.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os

# Accès aux modules de base
sys.path.append(os.path.abspath("../../PlutoDoppler"))
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator

# 1. Configuration du test
fs = 2_000_000          # Taux d'échantillonnage (2 MHz)
fc = 2_100_000_000      # Fréquence centrale (2.1 GHz)
n_samples = 4096        # Taille du Chirp (nombre d'échantillons)
bw = 20_000_000         # Bande passante (20 MHz)

# 2. Initialisation matérielle
hw = PlutoDevice(fs=fs, lo=fc)
hw.sdr.rx_buffer_size = n_samples * 4  # Capture large pour ne pas rater le début
hw.sdr.tx_hardwaregain_chan0 = -30     # Puissance TX modérée pour le câble
hw.set_rx_gain('manual', 30)           # Gain RX standard

# 3. Génération et capture du signal
chirp_tx = SignalGenerator.generate_chirp(fs, n_samples, bw)
hw.tx(chirp_tx)
rx_data = hw.rx()                      # On capture un bloc d'échantillons
hw.stop_tx()

# 4. Préparation des axes temporels
t_tx = np.arange(len(chirp_tx)) / fs * 1000  # Temps en ms pour le TX
t_rx = np.arange(len(rx_data)) / fs * 1000   # Temps en ms pour le RX

# 5. Visualisation instrumentée
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Graphique Émission (TX)
ax1.plot(t_tx, np.real(chirp_tx), color='#00d4ff', label="Composante Réelle (I)")
ax1.set_title("SIGNAL ÉMIS (CHIRP NUMÉRIQUE)", color='cyan', fontsize=12)
ax1.set_xlabel("Temps (ms)", fontsize=10)
ax1.set_ylabel("Amplitude (Normalisée)", fontsize=10)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(loc='upper right')

# Graphique Réception (RX)
ax2.plot(t_rx, np.real(rx_data), color='#ff9900', label="Signal Capturé via Câble")
ax2.set_title("SIGNAL REÇU (CAPTÉ PAR LE PLUTOSDR)", color='orange', fontsize=12)
ax2.set_xlabel("Temps (ms)", fontsize=10)
ax2.set_ylabel("Amplitude (Volt relative)", fontsize=10)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.legend(loc='upper right')

plt.tight_layout()
plt.show()