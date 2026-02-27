import numpy as np
import adi
import matplotlib.pyplot as plt
import time

# --- 1. CONFIGURATION ---
IP_ADDRESS = "ip:192.168.2.1"
sdr = adi.Pluto(IP_ADDRESS)
sdr.tx_destroy_buffer()
sdr.tx_cyclic_buffer = False

sdr.sample_rate = 1000000
sdr.tx_lo = int(800e6)
sdr.rx_lo = int(800e6)
sdr.tx_hardwaregain_chan0 = -20
sdr.rx_hardwaregain_chan0 = 30.0 
sdr.rx_buffer_size = 100000 

# --- 2. MESSAGE + BRUIT ---
message = "QPSK OK! Ca marche enfin." 
print(f"📧 Message : '{message}'")

# Message -> Bits
msg_bits = []
for char in message:
    bin_val = bin(ord(char))[2:].zfill(8)
    msg_bits.extend([int(b) for b in bin_val])

# Balise
barker_bits = [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0] 

# Bruit (Beaucoup de bruit pour bien définir la ligne de phase)
np.random.seed(123)
noise_head = np.random.randint(0, 2, 2000).tolist()
noise_tail = np.random.randint(0, 2, 2000).tolist()

full_bits = noise_head + barker_bits + msg_bits + noise_tail
if len(full_bits) % 2 != 0: full_bits.append(0)

# Mapping
qpsk_symbols = []
for i in range(0, len(full_bits), 2):
    b1, b2 = full_bits[i], full_bits[i+1]
    qpsk_symbols.append(complex(1 if b1==0 else -1, 1 if b2==0 else -1))

# Émission
sps = 16
iq_tx = np.repeat(qpsk_symbols, sps) * 2**14

print("📡 Émission...")
sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))
time.sleep(1)

# --- 3. RÉCEPTION ---
rx_samples = sdr.rx()
sdr.tx_destroy_buffer()

# --- 4. CORRECTION "DE-SPINNER" (NOUVEAU) ---
print("🔧 Correction Linéaire de Phase...")

# 1. Puissance 4 pour tuer la modulation (les 4 points deviennent 1)
# Cela révèle la dérive de fréquence pure
signal_p4 = rx_samples**4

# 2. On extrait l'angle instantané et on le "déroule" (Unwrap)
# Sans unwrap, l'angle saute de 360 à 0, on veut une ligne continue
phase_evolution = np.unwrap(np.angle(signal_p4))

# 3. On calcule la pente moyenne de cette phase (Régression linéaire)
# x = temps (indices), y = phase
x = np.arange(len(phase_evolution))
slope, intercept = np.polyfit(x, phase_evolution, 1)

# La pente nous donne la vitesse de rotation par échantillon
freq_drift_per_sample = slope / 4.0 # Divisé par 4 car puissance 4
print(f"   -> Pente détectée : {slope:.5f} rad/sample")

# 4. On génère le signal de "contre-rotation"
correction_vector = np.exp(-1j * freq_drift_per_sample * x)
rx_derotated = rx_samples * correction_vector

# --- 5. FINITION (PHASE STATIQUE & SYNCHRO) ---

# Maintenant que le signal est "droit", on corrige l'angle constant restant
angle_final = np.angle(np.mean(rx_derotated**4)) / 4
rx_final = rx_derotated * np.exp(-1j * angle_final)

# Synchro Temporelle (Offset)
best_std = float('inf')
best_offset = 0
for offset in range(sps):
    pts = rx_final[offset::sps]
    sample_pts = pts[:2000]
    std = np.std(np.abs(sample_pts) - np.mean(np.abs(sample_pts)))
    if std < best_std:
        best_std = std
        best_offset = offset

final_points = rx_final[best_offset::sps]

# --- 6. DÉCODAGE ---
print("🔍 Recherche Barker...")

target_barker = []
for i in range(0, len(barker_bits), 2):
    b1, b2 = barker_bits[i], barker_bits[i+1]
    target_barker.append(complex(1 if b1==0 else -1, 1 if b2==0 else -1))
target_barker = np.array(target_barker)

found_text = "ECHEC"
final_constellation = final_points

for rot in [0, 1, 2, 3]:
    test_points = final_points * (1j**rot)
    
    corr = np.abs(np.correlate(test_points, target_barker, mode='valid'))
    peak = np.max(corr)
    
    if peak > 12: # Seuil strict
        idx = np.argmax(corr)
        start_msg = idx + len(target_barker)
        num_symbols_msg = len(msg_bits) // 2
        msg_syms = test_points[start_msg : start_msg + num_symbols_msg]
        
        rx_bits = []
        for p in msg_syms:
            rx_bits.append(0 if p.real > 0 else 1)
            rx_bits.append(0 if p.imag > 0 else 1)
            
        chars = []
        try:
            for i in range(0, len(rx_bits), 8):
                byte = rx_bits[i:i+8]
                val = int("".join(map(str, byte)), 2)
                chars.append(chr(val))
            found_text = "".join(chars)
            print(f"🎉 TROUVÉ : {found_text}")
            final_constellation = test_points
            break
        except: pass

# --- 7. AFFICHAGE DE LA PREUVE ---
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
# On montre l'évolution de la phase pour prouver qu'elle dérivait
plt.plot(phase_evolution[:1000], label="Phase brute (Zoom)")
plt.plot(x[:1000]*slope + intercept, 'r--', label="Pente détectée")
plt.title("Pourquoi le 'U' ? (Dérive de Phase)")
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.scatter(final_constellation.real, final_constellation.imag, s=2, alpha=0.2, color='blue', label='Bruit')
# Message en rouge
idx_start = len(noise_head)//2
idx_end = idx_start + len(msg_bits)//2
if len(final_constellation) > idx_end:
    plt.scatter(final_constellation.real[idx_start:idx_end], final_constellation.imag[idx_start:idx_end], s=10, color='red', label='Message')

plt.title(f"Résultat : {found_text}")
plt.axis('equal'); plt.grid(True)
plt.legend()
plt.show()

del sdr