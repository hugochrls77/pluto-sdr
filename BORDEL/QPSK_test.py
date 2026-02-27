import numpy as np
import adi
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
sample_rate = 1e6 
center_freq = 915e6 
num_samps = 20000 # On capture un peu plus pour être sûr d'avoir tout le message

sdr = adi.Pluto("usb:1.4.5")
sdr.sample_rate = int(sample_rate)
sdr.tx_lo = int(center_freq)
sdr.tx_hardwaregain_chan0 = -10 
sdr.rx_lo = int(center_freq)
sdr.rx_buffer_size = num_samps
sdr.gain_control_mode_chan0 = 'manual'
sdr.rx_hardwaregain_chan0 = 60.0 

# --- 1. GÉNÉRATION DU SIGNAL THÉORIQUE ---
num_symbols = 1000
# On garde x_int en mémoire pour comparer à la fin
x_int_sent = np.random.randint(0, 4, num_symbols) 
x_radians = (x_int_sent * 90 + 45) * np.pi / 180.0
x_symbols_sent = np.cos(x_radians) + 1j*np.sin(x_radians)

# Signal "Théorique" (sans bruit, avant passage dans la radio)
samples_tx = np.repeat(x_symbols_sent, 16) 
samples_tx_scaled = samples_tx * 2**14 

# --- 2. TRANSMISSION ET RÉCEPTION ---
sdr.tx_cyclic_buffer = True
sdr.tx(samples_tx_scaled)
for i in range(10): _ = sdr.rx() # On vide les buffers
rx_samples = sdr.rx()
sdr.tx_destroy_buffer()

# --- 3. SYNCHRONISATION (Corrigée) ---
correlation = np.abs(np.correlate(rx_samples / np.max(rx_samples), samples_tx, mode='full'))
delay = np.argmax(correlation) - len(samples_tx) + 1

# On extrait ce qu'on a pu capturer
rx_aligned = rx_samples[delay : delay + len(samples_tx)]

# --- 4. DÉCODAGE ---
# On récupère les symboles (un point tous les 16)
rx_symbols = rx_aligned[8::16] 

# /!\ AJUSTEMENT DE LA TAILLE /!\
# On ne garde du signal d'origine que ce qu'on a vraiment reçu
min_len = min(len(x_int_sent), len(rx_symbols))
x_int_sent_final = x_int_sent[:min_len]
rx_symbols = rx_symbols[:min_len]

# Décodage des angles
angles = np.angle(rx_symbols)
x_int_decoded = np.round((angles * 180 / np.pi - 45) / 90) % 4
x_int_decoded = x_int_decoded.astype(int)

# --- 5. COMPARAISON ET AFFICHAGE ---
plt.figure(figsize=(12, 10))

# A. Comparaison Temporelle
plt.subplot(3, 1, 1)
plt.plot(samples_tx.real[:200], label='Théorique (TX)', color='green', linestyle='--')
rx_norm = rx_aligned.real / (np.max(np.abs(rx_aligned)) + 1e-9)
plt.plot(rx_norm[:200], label='Reçu (RX)', color='blue', alpha=0.7)
plt.title(f"Comparaison Temporelle (Délai détecté : {delay} échantillons)")
plt.legend()

# B. Comparaison des Symboles
plt.subplot(3, 1, 2)
plt.step(range(min(50, min_len)), x_int_sent_final[:50], where='post', label='Envoyé', color='black', alpha=0.5)
plt.plot(range(min(50, min_len)), x_int_decoded[:50], 'ro', label='Décodé', markersize=4)
plt.title(f"Comparaison des Symboles ({min_len} symboles comparés)")
plt.legend()

# C. Résultats
errors = np.sum(x_int_sent_final != x_int_decoded)
print(f"--- RÉSULTATS ---")
print(f"Signal trouvé au délai : {delay}")
print(f"Symboles comparés : {min_len} / {num_symbols}")
print(f"Erreurs détectées : {errors}")
if min_len > 0:
    print(f"Taux d'erreur symbole (SER) : {(errors/min_len)*100:.2f}%")

plt.tight_layout()
plt.show()