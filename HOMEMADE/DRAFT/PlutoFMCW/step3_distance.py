# HOMEMADE/DRAFT/PlutoFMCW/step3_distance.py
import numpy as np
import matplotlib.pyplot as plt
import sys, os

# Accès aux modules de base
sys.path.append(os.path.abspath("../../PlutoDoppler"))
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator

# 1. Configuration (Gardons les mêmes paramètres pour la continuité)
fs, fc, n_samples, bw = 2_000_000, 2_100_000_000, 4096, 20_000_000

# 2. Acquisition (Câble SMA branché)
hw = PlutoDevice(fs=fs, lo=fc)
hw.sdr.rx_buffer_size = n_samples * 4
hw.sdr.tx_hardwaregain_chan0 = -30
hw.set_rx_gain('manual', 30)

chirp_tx = SignalGenerator.generate_chirp(fs, n_samples, bw)
hw.tx(chirp_tx)
rx_data = hw.rx()
hw.stop_tx()

# 3. SYNCHRONISATION (Phase 2 réintégrée)
correlation = np.abs(np.correlate(rx_data, chirp_tx, mode='valid'))
offset_samples = np.argmax(correlation)
rx_aligned = rx_data[offset_samples : offset_samples + n_samples]

# 4. DECHIRPING (Phase 3 : Le cœur du radar)
# On multiplie le RX aligné par le conjugué du TX
beat_signal = rx_aligned * np.conj(chirp_tx)

# 5. CALCUL DE LA RANGE FFT (Transformation en mètres)
# On applique une fenêtre de Blackman pour éviter les lobes secondaires
window = np.blackman(n_samples)
range_fft = np.fft.fft(beat_signal * window)
range_fft = np.abs(range_fft[:n_samples//2])
range_db = 20 * np.log10(range_fft / n_samples + 1e-12)

# Axe des distances : 1 bin = c / (2 * BW)
dist_axis = np.arange(len(range_db)) * (299792458 / (2 * bw))

# 6. VISUALISATION INSTRUMENTÉE
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Le signal de battement (Beat Signal)
t_ms = np.arange(n_samples) / fs * 1000
ax1.plot(t_ms, np.real(beat_signal), color='#00d4ff')
ax1.set_title("SIGNAL DE BATTEMENT (BEAT NOTE)", color='cyan', fontsize=12)
ax1.set_xlabel("Temps (ms)", fontsize=10)
ax1.set_ylabel("Amplitude Réelle", fontsize=10)
ax1.grid(True, alpha=0.3)

# Le Spectre de Distance
ax2.plot(dist_axis, range_db, color='#ff0055', lw=2)
ax2.set_title("PHASE 3 : SPECTRE DE DISTANCE (RANGE FFT)", color='orange', fontsize=12)
ax2.set_xlabel("Distance apparente (mètres)", fontsize=10)
ax2.set_ylabel("Puissance (dBFS)", fontsize=10)
ax2.set_xlim(0, 100) # On regarde jusqu'à 100m
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()