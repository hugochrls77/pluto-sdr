import adi
import matplotlib.pyplot as plt
import numpy as np
import time
import datetime

# --- 1. CONFIGURATION ---
IP_ADDRESS = "ip:192.168.2.1"
sdr = adi.Pluto(IP_ADDRESS)

sdr.sample_rate = 10000000       # 2 MHz pour capturer plus d'énergie par point
sdr.tx_hardwaregain_chan0 = -10 # Attention : avec le câble, ne pas monter trop haut
sdr.rx_hardwaregain_mode = 'manual'
sdr.rx_hardwaregain_chan0 = 60 # Gain RX modéré pour le câble

# --- 2. GÉNÉRATION DES FRÉQUENCES LOGARITHMIQUES ---
# De 70 MHz à 6 GHz
start_f = 70e6
stop_f = 6000e6
num_points = 150  # 150 points suffisent pour une vue globale log
frequencies = np.geomspace(start_f, stop_f, num_points)

# Statistiques réduites pour la vitesse (3 passages suffisent pour un profil global)
n_scans = 5
n_captures = 5
results_matrix = np.zeros((len(frequencies), n_scans * n_captures))

# --- 3. SIGNAL DE TEST ---
fs = sdr.sample_rate
t = np.arange(0, 1024)
iq_tx = 30000 * np.exp(2j * np.pi * 100000 * t / fs)
sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))

print(f"📡 Scan LOG de {start_f/1e6:.0f} MHz à {stop_f/1e6:.0f} MHz")
start_time = time.time()

# --- 4. BOUCLE DE SCAN ---
try:
    for s in range(n_scans):
        print(f"Passage {s+1}/{n_scans}...")
        for i, f in enumerate(frequencies):
            sdr.tx_lo = int(f)
            sdr.rx_lo = int(f)
            time.sleep(0.02) # Temps de verrouillage PLL réduit (hack plus rapide)
            
            for c in range(n_captures):
                idx = s * n_captures + c
                samples = sdr.rx()
                results_matrix[i, idx] = np.max(np.abs(samples))
except KeyboardInterrupt:
    print("Interrompu.")

# --- 5. TRAITEMENT ---
moyennes = np.mean(results_matrix, axis=1)
mins = np.min(results_matrix, axis=1)
maxs = np.max(results_matrix, axis=1)

# --- 6. AFFICHAGE LOGARITHMIQUE ---
plt.figure(figsize=(14, 7))

# Rendu avec échelle X logarithmique
plt.fill_between(frequencies, mins, maxs, color='gray', alpha=0.2)
plt.semilogx(frequencies, moyennes, color='red', linewidth=1.5, label='Réponse fréquentielle (Log)')

# Formatage des axes pour la clarté
plt.title(f"Scan Large Bande (Hack 70MHz-6GHz) - {datetime.date.today()}")
plt.xlabel("Fréquence [Hz] - Échelle Log")
plt.ylabel("Amplitude")
plt.grid(True, which="both", ls="-", alpha=0.5)

# Ajout de labels pour les bandes clés
bands = [100e6, 800e6, 1800e6, 2400e6, 5000e6]
for b in bands:
    plt.axvline(b, color='green', alpha=0.3, linestyle='--')

plt.legend()
plt.show()

sdr.tx_destroy_buffer()
del sdr