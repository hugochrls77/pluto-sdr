import adi
import numpy as np
import time

# 1. Connexion au Pluto
try:
    sdr = adi.Pluto("ip:192.168.2.1")
except:
    print("Impossible de se connecter au Pluto. Vérifie l'IP.")
    exit()

# 2. Paramètres Radio
sdr.sample_rate = 1000000    # 1 MHz
sdr.tx_lo = int(915e6)      # 1 GHz (Fréquence centrale)
sdr.tx_hardwaregain_chan0 = -10 # Puissance (0 = Max, -10 est une bonne valeur de test)

# 3. Création du Sinus
# On crée une onde complexe décalée de 100 kHz du centre
# Cela évite les parasites au centre de la fréquence (le "DC offset")
fs = sdr.sample_rate
f_offset = 100000 # 100 kHz
t = np.arange(0, 1024) / fs
iq_tx = 2**14 * np.exp(2j * np.pi * f_offset * t)

# 4. Émission en continu (Mode Cyclique)
# Le Pluto va répéter ces 1024 points indéfiniment tout seul
sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))

print(f"📡 Émission lancée à {sdr.tx_lo / 1e6} MHz + {f_offset/1e3} kHz d'offset.")
print("Appuie sur Ctrl+C pour arrêter.")

# 5. On garde le script vivant
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nArrêt de l'émission...")
    sdr.tx_destroy_buffer() # Très important pour arrêter l'émission proprement
    del sdr