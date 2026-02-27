import adi
import matplotlib.pyplot as plt
import numpy as np
import time

# 1. Connexion propre
try:
    sdr = adi.Pluto("usb:1.4.5")
    sdr.tx_destroy_buffer() # On nettoie d'éventuels restes
except:
    print("Erreur : Le Pluto est déjà utilisé ou débranché.")
    exit()

# 2. Paramètres de puissance MAXIMUM
fs = 2000000
sdr.sample_rate = fs
sdr.tx_lo = 434000000
sdr.rx_lo = 434000000

sdr.tx_hardwaregain = 0      # 0 dB = Puissance maximale sur Pluto
sdr.rx_hardwaregain_mode = 'fast_attack'
sdr.rx_hardwaregain = 70     # Gain RX très élevé pour être sûr d'entendre

# 3. Signal très marqué (Offset de 400 kHz)
f_offset = 400000
t = np.arange(0, 1024) / fs
iq_tx = 2**14 * np.exp(2j * np.pi * f_offset * t)

sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))

# 4. Petite pause pour laisser le hardware se stabiliser
time.sleep(0.5)

# 5. Capture et vérification du niveau
samples = sdr.rx()
max_amp = np.max(np.abs(samples))
print(f"Amplitude max reçue : {max_amp:.2f}")

if max_amp < 50:
    print("ATTENTION : Le signal est très faible. Vérifie tes antennes !")

# 6. Graphique simplifié (sans la gomme pour voir la réalité)
psd = np.abs(np.fft.fftshift(np.fft.fft(samples)))
psd_db = 20 * np.log10(psd / len(psd))
freqs = np.linspace(-fs/2, fs/2, len(psd))

plt.figure(figsize=(10, 5))
plt.plot(freqs / 1e3, psd_db)
plt.axvline(x=f_offset/1e3, color='r', label="Cible (400kHz)")
plt.title(f"Diagnostic - Amplitude Max: {max_amp:.1f}")
plt.ylim(-40, 40) # On fixe l'échelle pour mieux comparer
plt.legend()
plt.grid()
plt.show()

sdr.tx_destroy_buffer()
del sdr