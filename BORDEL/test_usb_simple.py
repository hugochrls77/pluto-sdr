import adi
print("🧪 Test USB Pluto simple...")

# Scan tous les devices USB disponibles
try:
    for i in range(10):
        try:
            sdr = adi.Pluto(f"usb:{i}.0.0")
            print(f"✅ USB {i} trouvé !")
            break
        except:
            continue
    else:
        print("❌ Aucun USB Pluto trouvé")
        exit()
        
    print("📡 Config FM...")
    sdr.sample_rate = 1000000
    sdr.rx_lo = 100e6
    sdr.rx_hardwaregain_chan0 = 30
    
    print("🎵 Réception 100MHz...")
    data = sdr.rx()
    print(f"🎉 {len(data)} échantillons reçus !")
    
except Exception as e:
    print(f"Erreur: {e}")
