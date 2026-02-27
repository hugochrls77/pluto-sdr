import adi
import numpy as np
import time
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION ---
IP_ADDRESS = "ip:192.168.2.1"
FREQ = 860e6  # Ta fréquence championne
SAMPLES_PER_SYMBOL = 16

sdr = adi.Pluto(IP_ADDRESS)
sdr.sample_rate = 1000000
sdr.tx_lo = int(FREQ)
sdr.rx_lo = int(FREQ)
sdr.tx_hardwaregain_chan0 = -10
sdr.rx_hardwaregain_chan0 = 60

# --- 2. ENCODAGE DU MESSAGE ---
message_a_envoyer = "HELLO_PLUTO"
# Conversion Texte -> Bits
bits = ''.join(format(ord(c), '08b') for c in message_a_envoyer)
bit_array = np.array([int(b) for b in bits])

# Modulation QPSK simple (Mapping)
symbols = []
for i in range(0, len(bit_array), 2):
    b1, b2 = bit_array[i], bit_array[i+1]
    symbols.append(complex(1 if b1==0 else -1, 1 if b2==0 else -1))

# Ajout d'un PRÉAMBULE (une balise connue pour la synchronisation)
preambule = np.array([1+1j]*32 + [-1-1j]*32) 
signal_complet = np.concatenate([preambule, symbols])

# Suréchantillonnage (chaque symbole dure 16 échantillons)
iq_tx = np.repeat(signal_complet, SAMPLES_PER_SYMBOL) * 2**14

# --- 3. TRANSMISSION ---
print(f"📡 Émission du message : '{message_a_envoyer}'...")
sdr.tx_cyclic = True
sdr.tx(iq_tx.astype(np.complex64))
time.sleep(0.5) # On laisse le temps au signal de se propager

# --- 4. RÉCEPTION (On capture plus large) ---
print("📥 Réception...")
# On augmente la taille du buffer pour être sûr de tout avoir
sdr.rx_buffer_size = 65536 
rx_data = sdr.rx()
sdr.tx_destroy_buffer() 

# --- 5. DÉCODAGE (Version Flexible) ---
preambule_scaled = np.repeat(preambule, SAMPLES_PER_SYMBOL)
correlation = np.abs(np.correlate(rx_data / np.max(rx_data), preambule_scaled, mode='full'))
start_index = np.argmax(correlation) - len(preambule_scaled) + 1

# On définit la zone du message
offset_message = start_index + len(preambule_scaled)
# On extrait les symboles reçus
extracted_samples = rx_data[offset_message + 8 :: SAMPLES_PER_SYMBOL]

# --- PROTECTION CONTRE LES TAILLES DIFFÉRENTES ---
# On prend le minimum entre ce qu'on a reçu et ce qu'on a envoyé
nb_symbols_recus = len(extracted_samples)
nb_symbols_attendus = len(symbols)
taille_commune = min(nb_symbols_recus, nb_symbols_attendus)

if taille_commune < 5: # Si on a presque rien reçu
    print(f"❌ Erreur : Message trop court ou non trouvé ({taille_commune} symboles).")
else:
    # On tronque les deux tableaux à la même taille pour éviter le ValueError
    symbols_at = np.array(symbols[:taille_commune])
    extracted_symbols = extracted_samples[:taille_commune]

    # Correction de Phase
    phase_correction = np.angle(np.mean(extracted_symbols / symbols_at))
    extracted_symbols *= np.exp(-1j * phase_correction)

    # Décision
    decoded_bits = []
    for s in extracted_symbols:
        decoded_bits.append(0 if s.real > 0 else 1)
        decoded_bits.append(0 if s.imag > 0 else 1)

    # Reconversion Bits -> Texte
    decoded_text = ""
    for i in range(0, len(decoded_bits) - 7, 8):
        byte = decoded_bits[i:i+8]
        char_code = int(''.join(map(str, byte)), 2)
        decoded_text += chr(char_code)

    print(f"\n✨ MESSAGE REÇU ({taille_commune}/{nb_symbols_attendus} symboles) :")
    print(f"👉 {decoded_text}")

# --- 6. VISUALISATION ---
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.plot(correlation)
plt.title("Synchronisation (Pic de corrélation)")
plt.subplot(1, 2, 2)
plt.scatter(extracted_symbols.real, extracted_symbols.imag, color='red')
plt.axhline(0, color='black')
plt.axvline(0, color='black')
plt.title("Constellation QPSK reçue")
plt.show()

del sdr