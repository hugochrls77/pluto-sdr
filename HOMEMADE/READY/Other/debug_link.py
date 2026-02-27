import adi
import numpy as np
import matplotlib.pyplot as plt
import time

# Test ultra-simplifié
sdr = adi.Pluto("ip:192.168.2.1")
fs = 2000000
sdr.sample_rate = fs
sdr.tx_lo = int(100e6)
sdr.rx_lo = int(100e6)
sdr.tx_hardwaregain_chan0 = -10
sdr.rx_hardwaregain_chan0 = 20.0

# On crée un signal très reconnaissable : un décalage de +500kHz
t = np.linspace(0, 0.1, int(fs*0.1))
iq_tx = np.exp(1j * 2 * np.pi * 500000 * t) * 2**14

print("🚀 Émission ET Réception simultanée...")
sdr.tx_cyclic_buffer = True
sdr.tx(iq_tx.astype(np.complex64))

time.sleep(1) # Attente
data = sdr.rx()

# Calcul de la puissance max
p_max = np.max(np.abs(data))
print(f"📊 Amplitude brute max reçue : {p_max}")

# Affichage FFT
plt.psd(data, NFFT=1024, Fs=fs/1e6)
plt.title(f"Test Direct - Amp Max: {p_max}")
plt.show()

sdr.tx_destroy_buffer()