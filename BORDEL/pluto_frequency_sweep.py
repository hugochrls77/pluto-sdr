import adi
import matplotlib.pyplot as plt
import numpy as np
import time
import csv
import datetime

# --- 1. CONFIGURATION DU MATÉRIEL ---
# On utilise l'IP pour la stabilité et le débridage AD9364
IP_ADDRESS = "ip:192.168.2.1"
sdr = adi.Pluto(IP_ADDRESS)

# Paramètres radio
sdr.sample_rate = 1000000       # 1 MHz
sdr.tx_hardwaregain_chan0 = -10 # Puissance d'émission
sdr.rx_hardwaregain_mode = 'manual'
sdr.rx_hardwaregain_chan0 = 60.0

# Gamme de fréquences (70 MHz à 6 GHz possible, mais on teste 100-2000 MHz)
start_f, stop_f, step_f = 100e6, 2000e6, 10e6
frequencies = np.arange(start_f, stop_f + step_f, step_f)

# Paramètres statistiques (5 passages de 5 captures = 25 points par freq)
n_scans = 5
n_captures = 5
total_val = n_scans * n_captures
results_matrix = np.zeros((len(frequencies), total_val))

# --- 2. PRÉPARATION DU SIGNAL DE TEST ---
# Un sinus pur décalé de 100 kHz pour éviter le "DC spike" central
fs = sdr.sample_rate
t = np.arange(0, 1024)
iq_tx = 2**14 * np.exp(2j * np.pi * 100000 * t / fs)

sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))

# --- 3. BOUCLE DE SCAN MULTI-PASSES ---
print(f"🚀 Lancement du scan global sur {len(frequencies)} points...")
print(f"📊 Total de {total_val} mesures par fréquence.")
start_time = time.time()

try:
    for s in range(n_scans):
        print(f"🔄 Passage n°{s+1}/{n_scans} en cours...")
        for i, f in enumerate(frequencies):
            sdr.tx_lo = int(f)
            sdr.rx_lo = int(f)
            
            # Temps de verrouillage PLL (50ms est un bon compromis)
            time.sleep(0.05)
            
            # Rafale de captures
            for c in range(n_captures):
                idx = s * n_captures + c
                samples = sdr.rx()
                results_matrix[i, idx] = np.max(np.abs(samples))

except KeyboardInterrupt:
    print("\n⚠️ Scan interrompu par l'utilisateur.")

# --- 4. TRAITEMENT DES DONNÉES ---
moyennes = np.mean(results_matrix, axis=1)
stds = np.std(results_matrix, axis=1)
mins = np.min(results_matrix, axis=1)
maxs = np.max(results_matrix, axis=1)

# --- 5. EXPORTATION CSV (Option 3) ---
date_str = datetime.datetime.now().strftime("%Y%m%d")
# Nommage cohérent : DATE_APPAREIL_TYPE_PLAGE
csv_filename = f"{date_str}_BetterCable_Sweep_100-2000MHz.csv"

with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Frequency_MHz', 'Mean', 'Std_Dev', 'Min', 'Max'])
    for i in range(len(frequencies)):
        writer.writerow([frequencies[i]/1e6, moyennes[i], stds[i], mins[i], maxs[i]])

print(f"\n✅ Scan terminé en {time.time() - start_time:.1f} secondes.")
print(f"📁 Données sauvegardées sous : {csv_filename}")

# --- 6. AFFICHAGE GRAPHIQUE ---
plt.figure(figsize=(12, 7))

# Zone grise : Enveloppe totale (Min/Max) pour détecter les parasites
plt.fill_between(frequencies / 1e6, mins, maxs, color='gray', alpha=0.15, label='Enveloppe Bruit (Min/Max)')

# Zone bleue : Écart-type (Stabilité du signal)
plt.fill_between(frequencies / 1e6, moyennes - stds, moyennes + stds, color='blue', alpha=0.3, label='Zone de Stabilité (±1 std)')

# Ligne principale : La moyenne
plt.plot(frequencies / 1e6, moyennes, color='blue', linewidth=1.5, label='Moyenne (25 points/freq)')

# Esthétique
plt.axhline(y=500, color='red', linestyle='--', alpha=0.5, label='Seuil de détection')
plt.title(f"Caractérisation du lien Meilleur Cable - {date_str}", fontsize=14)
plt.xlabel("Fréquence [MHz]", fontsize=12)
plt.ylabel("Amplitude Reçue", fontsize=12)
plt.grid(True, which='both', linestyle=':', alpha=0.6)
plt.legend(loc='upper right')

plt.show()

# Nettoyage final
sdr.tx_destroy_buffer()
del sdr