import adi
import matplotlib.pyplot as plt
import numpy as np

# 1. Connexion au Pluto via l'adresse USB que tu as trouvée
try:
    sdr = adi.Pluto("usb:1.21.5")
    print("Succès ! Le Pluto est connecté via USB.")
except:
    print("Erreur : Vérifie que le Pluto est bien branché sur le même port.")

# 2. Configuration pour capter la Radio FM
sdr.sample_rate = 2000000
sdr.rx_lo = int(433.92e6)  # 433.92 MHz
sdr.rx_rf_bandwidth = 2000000
sdr.rx_buffer_size = 10000   # On prend un gros bloc de données

# 3. Capture des signaux
samples = sdr.rx()

# 4. Affichage simple pour comprendre ce qu'on reçoit
print(f"Nombre d'échantillons reçus : {len(samples)}")
print(f"Type de données : {type(samples[0])}") # Tu vas voir 'numpy.complex128'

# 5. Visualisation rapide (Amplitude dans le temps)
plt.plot(np.real(samples[:500])) # On affiche les 500 premiers points réels (I)
plt.title("Signal brut reçu (Composante I)")
plt.xlabel("Temps")
plt.ylabel("Amplitude")
plt.show()

del sdr