import adi
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURATION HARDWARE (Câble) ---
IP_ADDRESS = "ip:192.168.2.1"
sdr = adi.Pluto(IP_ADDRESS)

# Paramètres optimisés pour le câble
fs = 4000000 # Sample rate 2 MHz
sdr.sample_rate = fs
sdr.tx_lo = int(800e6)
sdr.rx_lo = int(800e6)

# Filtrage serré pour un signal propre
sdr.tx_rf_bandwidth = int(500000)
sdr.rx_rf_bandwidth = int(500000)

# Gains "pro" pour câble (Fort en TX, faible en RX)
sdr.tx_hardwaregain_chan0 = -20
sdr.rx_hardwaregain_mode = 'manual'
sdr.rx_hardwaregain_chan0 = 20

# --- GÉNÉRATION DU SIGNAL PARFAIT ---
f_offset = 100000 # 100 kHz
# On garde ta taille géante pour assurer la continuité cyclique
N_tx = 2048000 
t_tx = np.arange(0, N_tx) / fs

# Amplitude proche du max (32000 sur 32767)
iq_tx = 32000 * np.exp(2j * np.pi * f_offset * t_tx)

print(f"Configuration : TX Buffer de {N_tx} points pour une continuité parfaite.")

# --- ÉMISSION ET RÉCEPTION ---
sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))

# On vide le buffer une fois pour être sûr
for _ in range(5): sdr.rx()
samples = sdr.rx() # Capture standard (env. 131k points)

# Sanity Check
amp_max = np.max(np.abs(samples))
print(f"Amplitude Max Reçue : {amp_max:.1f} (Objectif: 2000 à 15000)")

# --- VISUALISATION DOUBLE VUE ---
fig = plt.figure(figsize=(14, 6)) # Fenêtre large

# === VUE 1 : Le Diagramme de Constellation (Le Cercle) ===
ax1 = fig.add_subplot(1, 2, 1)
# On n'affiche "que" 20000 points pour ne pas faire ramer l'affichage
N_plot_iq = 20000 
ax1.plot(samples[:N_plot_iq].real, samples[:N_plot_iq].imag, '.', markersize=1, color='#0066FF', alpha=0.2)
ax1.set_title(f"Vue 1 : Constellation I/Q (Santé globale)\nAmplitude Max: {amp_max:.0f}")
ax1.set_xlabel("I (In-Phase)")
ax1.set_ylabel("Q (Quadrature)")
ax1.axis('equal') # CRUCIAL : pour que le cercle soit rond
ax1.grid(True, linestyle=':', color='gray', alpha=0.5)
# On trace les axes centraux
ax1.axhline(0, color='black', linewidth=0.5)
ax1.axvline(0, color='black', linewidth=0.5)

# === VUE 2 : Le Domaine Temporel (Les Courbes) ===
ax2 = fig.add_subplot(1, 2, 2)
# On ZOOM sur quelques cycles seulement (ex: 400 points)
N_zoom = 200
t_zoom = np.arange(N_zoom)
ax2.plot(t_zoom, samples[:N_zoom].real, label='Canal I (Réel)', color='red', linewidth=2, alpha=0.8)
ax2.plot(t_zoom, samples[:N_zoom].imag, label='Canal Q (Imaginaire)', color='green', linewidth=2, alpha=0.8)
ax2.set_title(f"Vue 2 : Zoom Temporel ({N_zoom} échantillons)")
ax2.set_xlabel("Temps (numéro d'échantillon)")
ax2.set_ylabel("Amplitude numérique")
ax2.legend(loc='upper right')
ax2.grid(True)

plt.tight_layout()
plt.show()

# Nettoyage
sdr.tx_destroy_buffer()
del sdr