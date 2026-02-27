# homemade/dual_lab.py
import adi
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import config as cfg
import signals as sig

# 1. Initialisation
sdr = adi.Pluto(cfg.IP_ADDRESS)
sdr.sample_rate = cfg.SAMPLE_RATE
sdr.tx_lo = cfg.CENTER_FREQ
sdr.rx_lo = cfg.CENTER_FREQ
sdr.tx_hardwaregain_chan0 = cfg.TX_GAIN
sdr.rx_hardwaregain_chan0 = cfg.RX_GAIN

# --- LE FIX ICI ---
# On force le buffer de réception à la taille de la FFT
sdr.rx_buffer_size = cfg.FFT_SIZE 
# ------------------

# 2. Émission (Sinus +500kHz)
print(f"📡 Émission sur {cfg.CENTER_FREQ/1e6} MHz...")
# On s'assure que le signal est assez long pour remplir le buffer
samples = sig.generate_sine_wave(cfg.SAMPLE_RATE, duration=0.1, freq=500000) * 2**14
sdr.tx_cyclic_buffer = True
sdr.tx(samples.astype(np.complex64))

# 3. Préparation Graphique
fig, ax = plt.subplots(figsize=(10, 6), facecolor='#121212')
ax.set_facecolor('black')
line, = ax.plot([], [], color='#00FFCC', lw=1.5)

# On règle les limites Y (dB)
ax.set_ylim(-200, 0)
ax.grid(True, color='gray', alpha=0.3)

# Calcul de l'axe X (Fréquences Absolues)
# On s'assure que freqs fait EXACTEMENT cfg.FFT_SIZE
freqs = (np.fft.fftshift(np.fft.fftfreq(cfg.FFT_SIZE, 1/cfg.SAMPLE_RATE)) + cfg.CENTER_FREQ) / 1e6
ax.set_xlim(freqs[0], freqs[-1])

ax.set_title(f"LABO DUAL : TX & RX ({cfg.CENTER_FREQ/1e6} MHz)", color='white')
ax.set_xlabel("Fréquence (MHz)", color='white')
ax.set_ylabel("Puissance (dB)", color='white')
ax.tick_params(colors='white')

# Fenêtre de pondération (calculée une seule fois pour la performance)
win = np.blackman(cfg.FFT_SIZE)

def update(frame):
    # Capture
    raw_data = sdr.rx()
    
    # Sécurité au cas où le Pluto renverrait une taille bizarre
    if len(raw_data) != cfg.FFT_SIZE:
        return line,

    # Traitement
    fft_norm = np.fft.fftshift(np.fft.fft(raw_data * win)) / (32768 * cfg.FFT_SIZE)
    psd = 20 * np.log10(np.abs(fft_norm) + 1e-12)
    
    line.set_data(freqs, psd)
    return line,

# Ajout de cache_frame_data=False pour supprimer le warning
ani = animation.FuncAnimation(fig, update, interval=30, blit=True, cache_frame_data=False)

plt.show()

# Clean up
sdr.tx_destroy_buffer()
del sdr