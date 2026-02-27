# HOMEMADE/DRAFT/PlutoFMCW/sim_fmcw.py
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION RADAR SIMULÉ ---
fs = 20_000_000       # 20 MHz de taux d'échantillonnage
duration = 0.001      # Durée du Chirp : 1 ms
bw = 50_000_000       # Bande passante : 50 MHz (Largeur du balayage)
c = 299792458         # Vitesse de la lumière

# --- 2. GÉNÉRATION DU SIGNAL ÉMIS (TX CHIRP) ---
t = np.arange(int(fs * duration)) / fs
# La fréquence varie de -BW/2 à +BW/2
k = bw / duration     # Pente du chirp (Hz/s)
tx_signal = np.exp(1j * np.pi * k * t**2)

# --- 3. SIMULATION DE L'ÉCHO (RX SIGNAL) ---
dist_target = 10.5    # On simule un objet à 10.5 mètres
delay = (2 * dist_target) / c
# Le signal reçu est une version retardée du signal émis
t_rx = t - delay
rx_signal = np.exp(1j * np.pi * k * t_rx**2) + np.random.normal(0, 0.1, len(t))

# --- 4. TRAITEMENT FMCW (DECHIRPING) ---
# On multiplie le reçu par le conjugué de l'émis
# Cela extrait la différence de fréquence (f_beat)
beat_signal = rx_signal * np.conj(tx_signal)

# --- 5. CALCUL DE LA DISTANCE (FFT) ---
n = len(beat_signal)
range_fft = np.fft.fft(beat_signal * np.blackman(n))
range_fft = np.abs(range_fft[:n//2])
range_db = 20 * np.log10(range_fft / n + 1e-6)

# Axe des distances : f_beat = (dist * 2 * K) / c
# Donc dist = (f_beat * c) / (2 * K)
freqs = np.fft.fftfreq(n, 1/fs)[:n//2]
dist_axis = (freqs * c) / (2 * k)

# --- 6. VISUALISATION ---
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(t*1000, np.real(beat_signal), color='#00d4ff')
ax1.set_title("Signal de Battement (Beat Note) dans le temps")
ax1.set_xlabel("Temps (ms)")

ax2.plot(dist_axis, range_db, color='#ff0055')
ax2.axvline(dist_target, color='white', linestyle='--', alpha=0.5, label=f"Cible à {dist_target}m")
ax2.set_title("Spectre des Distances (Range FFT)")
ax2.set_xlabel("Distance (mètres)")
ax2.set_ylabel("Puissance (dB)")
ax2.set_xlim(0, 30) # On regarde les 30 premiers mètres
ax2.legend()

plt.tight_layout()
plt.show()