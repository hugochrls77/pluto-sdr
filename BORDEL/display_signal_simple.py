import adi
import numpy as np
import time

# 1. Connexion
sdr = adi.Pluto("usb:1.21.5")

# 2. Configuration Émetteur (TX)
fs = 2000000 # Taux d'échantillonnage (2 MHz)
sdr.tx_lo = 434000000 # Fréquence centrale à 434 MHz
sdr.tx_hardwaregain_mode = 'manual'
sdr.tx_hardwaregain = -10 # Puissance (attention, pas trop fort ! -10dB c'est bien)

# 3. Création du signal (un simple sinus décalé de 100 kHz)
fc = 100000 # Fréquence du "bip"
t = np.arange(0, 1024) / fs
# On crée un signal complexe : I + jQ
samples = 2**14 * np.exp(2j * np.pi * fc * t) 
samples = samples.astype(np.complex64)

# 4. Émission en boucle
print("Émission en cours à 434 MHz + 100 kHz...")
print("Appuie sur Ctrl+C pour arrêter.")

try:
    while True:
        sdr.tx(samples) # Envoie les données au buffer de transmission
except KeyboardInterrupt:
    print("\nArrêt de l'émission.")
    del sdr