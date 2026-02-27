import adi
import numpy as np

print("🔍 Test connexion Pluto...")

try:
    # Test 1: IP réseau
    sdr = adi.Pluto()
    print("✅ Connexion IP réussie !")
    
except:
    try:
        # Test 2: USB direct
        sdr = adi.Pluto()
        print("✅ Connexion USB réussie !")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        exit()

# Configuration réception FM
sdr.sample_rate = 1000000      # 1 Msps
sdr.rx_lo = 100000000          # 100 MHz
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 40

# Récupère des échantillons
samples = sdr.rx()
print(f"📡 {len(samples)} échantillons reçus !")
print("🎉 Pluto fonctionne parfaitement !")

sdr.rx_destroy_buffer()
