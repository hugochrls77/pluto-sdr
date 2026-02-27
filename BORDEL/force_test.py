import adi
import matplotlib.pyplot as plt
import numpy as np
import time

# 1. Connexion IP
sdr = adi.Pluto("ip:192.168.2.1")

# 2. Paramètres du scan
start_freq = 100e6   # 100 MHz (maintenant possible grâce au hack !)
stop_freq = 2000e6   # 2 GHz
step = 10e6          # Paliers de 50 MHz
frequencies = np.arange(start_freq, stop_freq + step, step)

# Configuration de base
sdr.sample_rate = 1000000
sdr.tx_hardwaregain_chan0 = -10
sdr.rx_hardwaregain_chan0 = 60
sdr.tx_cyclic = True

# Signal à émettre (un simple sinus à 100kHz d'offset)
fs = sdr.sample_rate
t = np.arange(0, 1024) / fs
iq_tx = 2**14 * np.exp(2j * np.pi * 100000 * t / fs)
sdr.tx(iq_tx.astype(np.complex64))

amplitudes = []

print(f"Début du scan de {start_freq/1e6:.0f} à {stop_freq/1e6:.0f} MHz...")

try:
    for f in frequencies:
        # On change la fréquence
        sdr.tx_lo = int(f)
        sdr.rx_lo = int(f)
        
        # On attend que le PLL se verrouille
        time.sleep(0.5)
        
        # On vide les buffers et on mesure
        for _ in range(5): _ = sdr.rx()
        samples = sdr.rx()
        
        amp = np.max(np.abs(samples))
        amplitudes.append(amp)
        print(f"Fréquence : {f/1e6:7.0f} MHz | Amplitude : {amp:.1f}")

except Exception as e:
    print(f"Erreur pendant le scan : {e}")

# --- AFFICHAGE DU RÉSULTAT ---
plt.figure(figsize=(10, 6))
plt.plot(frequencies / 1e6, amplitudes, marker='o', linestyle='-', color='teal')
plt.title("Efficacité du lien Radio en fonction de la Fréquence")
plt.xlabel("Fréquence [MHz]")
plt.ylabel("Amplitude Max reçue")
plt.grid(True, alpha=0.3)
plt.axhline(y=500, color='r', linestyle='--', label='Seuil de détection clair')
plt.legend()
plt.show()

sdr.tx_destroy_buffer()
del sdr