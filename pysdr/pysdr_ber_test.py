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
sdr.tx_hardwaregain_chan0 = -15
# On monte un peu le gain RX car tu étais à 695 (un peu faible)
sdr.rx_hardwaregain_chan0 = 40.0 
sdr.rx_buffer_size = 100000

# --- 2. PRÉPARATION ---
# Barker (Balise)
barker_bits = np.array([1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1])
barker_syms = np.array([complex(1,1) if b else complex(-1,-1) for b in barker_bits])

# Données
N_data_bits = 1000
np.random.seed(42)
tx_bits = np.random.randint(0, 2, N_data_bits)
data_syms = []
for i in range(0, len(tx_bits), 2):
    b1, b2 = tx_bits[i], tx_bits[i+1]
    data_syms.append(complex(1 if b1==0 else -1, 1 if b2==0 else -1))

full_sequence = np.concatenate([barker_syms, data_syms])
sps = 16
iq_tx = np.repeat(full_sequence, sps) * 2**14

# --- 3. ÉMISSION ---
print("📡 Émission...")
sdr.tx_cyclic_buffer = True
sdr.tx(iq_tx.astype(np.complex64))
time.sleep(1)

rx_samples = sdr.rx()
sdr.tx_destroy_buffer()
print(f"✅ Amplitude reçue : {np.max(np.abs(rx_samples)):.0f}")

# --- 4. TRAITEMENT ---

# A. Correction de Phase (Puissance 4)
angle = np.angle(np.mean(rx_samples**4)) / 4
rx_corrected = rx_samples * np.exp(-1j * angle)

# --- CORRECTIF CRUCIAL : ROTATION DE 45° ---
# Tes points étaient sur les axes (+), on les pousse dans les coins (X)
rx_corrected = rx_corrected * np.exp(1j * np.pi / 4) 
# -------------------------------------------

# B. Synchro Temporelle
best_std = float('inf')
best_offset = 0
for offset in range(sps):
    pts = rx_corrected[offset::sps]
    std = np.std(np.abs(pts) - np.mean(np.abs(pts)))
    if std < best_std:
        best_std = std
        best_offset = offset

rx_decimated = rx_corrected[best_offset::sps]

# C. Recherche Balise
# On met aussi la balise de référence à 45° pour que ça matche
barker_rotated = barker_syms * np.exp(1j * np.pi / 4) 
corr = np.abs(np.correlate(rx_decimated, barker_rotated, mode='full'))
start_index = np.argmax(corr) - len(barker_rotated) + 1

payload_start = start_index + len(barker_rotated)
rx_payload = rx_decimated[payload_start : payload_start + len(data_syms)]

# --- 5. DÉCODEUR UNIVERSEL ---
print("\n🕵️  Recherche de la configuration 0% erreur...")

best_ber = 100.0
final_points = rx_payload

# On garde ta boucle magique qui teste les 4 orientations
for rot in [0, 1, 2, 3]:
    for invert in [False, True]:
        pts_test = rx_payload * (1j**rot) # Teste 0, 90, 180, 270
        
        bits_test = []
        for p in pts_test:
            val_i = 0 if p.real > 0 else 1
            val_q = 0 if p.imag > 0 else 1
            if invert:
                val_i = 1 - val_i
                val_q = 1 - val_q
            bits_test.extend([val_i, val_q])
            
        bits_arr = np.array(bits_test)[:len(tx_bits)]
        if len(bits_arr) == len(tx_bits):
            ber = (np.sum(tx_bits != bits_arr) / len(tx_bits)) * 100
            if ber < best_ber:
                best_ber = ber
                final_points = pts_test

# --- 6. RÉSULTATS ---
print(f"📉 BER FINAL : {best_ber:.2f} %")

fig, (ax1,ax2) = plt.subplots(1, 2, figsize=(7, 14))
color = 'green' if best_ber < 1 else 'red'
ax1.scatter(final_points.real, final_points.imag, s=10, color=color, alpha=0.5)
lim = len(final_points.real)
ax2.plot(final_points.real[:lim],'.')
ax2.plot(final_points.imag[:lim],'.')
# On dessine les axes pour prouver que les points ne sont plus dessus
ax1.axhline(0, color='black', alpha=0.5)
ax1.axvline(0, color='black', alpha=0.5)
ax1.set_title(f"Constellation Finale (BER={best_ber:.2f}%)")
plt.grid()
plt.show()

del sdr