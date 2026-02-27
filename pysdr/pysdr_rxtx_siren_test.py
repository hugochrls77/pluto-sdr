import numpy as np
import adi
import matplotlib.pyplot as plt
import time
import scipy.signal as signal # Pour le filtrage propre

# --- 1. CONFIGURATION ---
IP_ADDRESS = "ip:192.168.2.1"
sdr = adi.Pluto(IP_ADDRESS)
sdr.tx_destroy_buffer()
sdr.tx_cyclic_buffer = False

# Fréquences
center_freq = 100000000 # 100 MHz
offset_freq = 250000    # On décale de 250 kHz (pour bien s'éloigner du centre)

sdr.tx_lo = center_freq
sdr.rx_lo = center_freq - offset_freq # RX calé à côté

sdr.sample_rate = 2400000 # 2.4 MSPS
sdr.tx_hardwaregain_chan0 = -10
sdr.rx_hardwaregain_chan0 = 50.0 # Gain Maximum ou presque
sdr.rx_buffer_size = 200000 # On double la taille pour voir plus de temps

# --- 2. SON RAPIDE (Pour être vu dans le buffer) ---
fs = sdr.sample_rate
duration = 1.0
t = np.linspace(0, duration, int(fs*duration))

# Une sirène très rapide (50 Hz d'oscillation) pour qu'on voie les vagues !
# Elle va faire "WouWouWouWou" 50 fois par seconde
audio_freq = 50 
audio_signal = np.sin(2 * np.pi * audio_freq * t) 

# --- 3. ÉMISSION ---
print("📡 Émission FM...")
f_dev = 75000 
iq_tx = np.exp(1j * 2 * np.pi * f_dev * np.cumsum(audio_signal) / fs)
iq_tx = iq_tx * 2**14

sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))
time.sleep(1)

# --- 4. RÉCEPTION & TRAITEMENT NUMÉRIQUE (DDC) ---
print(f"👂 Capture...")
rx_samples = sdr.rx()

# A. RECENTRAGE (Digital Down Converter)
# Le signal est à +250kHz. On le ramène mathématiquement à 0Hz.
t_rx = np.arange(len(rx_samples)) / fs
shifter = np.exp(-1j * 2 * np.pi * offset_freq * t_rx)
rx_baseband = rx_samples * shifter # Le pic est maintenant à 0Hz !

# B. DECIMATION (Le secret de la propreté)
# On passe de 2.4 MHz à 48 kHz (Standard Audio). Facteur 50.
# Cela élimine tout le bruit haute fréquence.
rx_decimated = signal.decimate(rx_baseband, 50) 
fs_new = fs / 50 # Nouvelle fréquence d'échantillonnage (48 kHz)

# C. DÉMODULATION
# On démodule sur le signal propre et lent
demod = np.angle(rx_decimated[1:] * np.conj(rx_decimated[:-1]))

# --- 5. AFFICHAGE ---
plt.figure(figsize=(10, 8))

# Spectre AVANT traitement (Pour confirmer la réception)
plt.subplot(3, 1, 1)
fft_sig = np.abs(np.fft.fftshift(np.fft.fft(rx_samples[:4096])))
freqs = np.linspace(-fs/2, fs/2, len(fft_sig))
plt.plot(freqs/1000, fft_sig)
plt.title(f"1. Spectre Brut (Signal attendu vers +{offset_freq/1000} kHz)")
plt.xlabel("kHz")
plt.grid(True)

# Audio Attendu
plt.subplot(3, 1, 2)
# On zoome sur la même durée que ce qu'on a reçu décimé
samples_to_show = 200 # Quelques vagues
plt.plot(audio_signal[:samples_to_show], color='blue', label='Envoyé')
plt.title("2. Forme de l'onde envoyée (Zoom)")
plt.grid(True)

# Audio Reçu
plt.subplot(3, 1, 3)
plt.plot(demod[:samples_to_show], color='green', label='Reçu')
plt.title("3. Audio Reçu Démodulé (Après filtrage)")
plt.grid(True)

plt.tight_layout()
plt.show()

sdr.tx_destroy_buffer()
del sdr