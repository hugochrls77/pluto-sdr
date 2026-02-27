import adi
import matplotlib.pyplot as plt
import numpy as np
import time

sdr = adi.Pluto("ip:192.168.2.1")

# 1. Paramètres de départ (plus réalistes pour un câble)
sdr.sample_rate = 2000000
sdr.tx_lo = int(800e6)
sdr.rx_lo = int(800e6)

# ON AUGMENTE ICI
sdr.tx_hardwaregain_chan0 = -30   # -30dB (au lieu de -50)
sdr.rx_hardwaregain_mode = 'manual'
sdr.rx_hardwaregain_chan0 = 40.0  # 20dB (au lieu de 10)

# 2. Signal Sinus
fs = sdr.sample_rate
t = np.arange(0, 2048000) / fs
iq_tx = 2**14 * np.exp(2j * np.pi * 100000 * t)

# 3. Émission
sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))
time.sleep(0.5)

# 4. Capture et vérification
samples = sdr.rx()
amp_max = np.max(np.abs(samples))

print(f"Test avec TX=-30 / RX=20 | Amplitude Max : {amp_max:.1f}")

if amp_max < 500:
    print("💡 C'est encore un peu faible. Tu peux essayer de passer sdr.rx_hardwaregain_chan0 à 30.0")
elif amp_max > 30000:
    print("⚠️ Attention, ça sature ! Baisse le gain RX.")

# 5. Affichage
plt.figure(figsize=(10, 5))
plt.plot(samples[:200].real, label="Signal Réel (I)")
plt.plot(samples[:200].imag, label="Signal Imaginaire (Q)", alpha=0.5)
plt.title(f"Liaison Câble - Amplitude : {amp_max:.1f}")
plt.grid(True)
plt.legend()
plt.show()

sdr.tx_destroy_buffer()
del sdr