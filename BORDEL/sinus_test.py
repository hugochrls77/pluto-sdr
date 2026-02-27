import adi
import matplotlib.pyplot as plt
import numpy as np
import time

# 1. Connexion IP
sdr = adi.Pluto("ip:192.168.2.1")

# 2. Paramètres "Gagnants" (ceux du test QPSK qui a marché)
sdr.sample_rate = 1000000
sdr.tx_lo = int(1000e6) 
sdr.rx_lo = int(1000e6)

# PUISSANCE MAXIMUM
sdr.tx_hardwaregain_chan0 = 0      # 0 dB est le maximum de puissance
sdr.rx_hardwaregain_mode = 'manual'
sdr.rx_hardwaregain_chan0 = 70.0   # Gain RX très élevé

# 3. Création du Signal
fs = sdr.sample_rate
f_offset = 200000 # +200 kHz
t = np.arange(0, 2048) / fs
iq_tx = 2**14 * np.exp(2j * np.pi * f_offset * t)

# 4. Émission cyclique
sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))

print("Attente de stabilisation...")
time.sleep(1) # On laisse 1 seconde au hardware

# 5. Capture avec vidage de buffer
for _ in range(20): _ = sdr.rx() 
samples = sdr.rx()

# 6. Analyse
amp_max = np.max(np.abs(samples))
print(f"Amplitude Max détectée : {amp_max}")

# --- AFFICHAGE ---
psd = np.abs(np.fft.fftshift(np.fft.fft(samples)))
psd_dB = 20 * np.log10(psd / len(psd))
freqs = np.linspace(-fs/2, fs/2, len(psd))

plt.figure(figsize=(10, 5))
plt.plot(freqs / 1e3, psd_dB)
plt.axvline(x=f_offset/1e3, color='r', linestyle='--')
plt.title(f"Test 915 MHz - Amplitude : {amp_max:.1f}")
plt.xlabel("kHz")
plt.grid(True)
plt.show()

sdr.tx_destroy_buffer()
del sdr