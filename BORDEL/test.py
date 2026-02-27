import adi
import matplotlib.pyplot as plt
import numpy as np

# Connexion via IP
try:
    sdr = adi.Pluto("ip:192.168.2.1")
    
    # 1. On descend ENFIN sous les 325 MHz
    sdr.rx_lo = int(94.3e6)  # 94.3 MHz
    sdr.sample_rate = int(2e6)
    sdr.rx_rf_bandwidth = int(200e3) # Largeur d'une station FM
    sdr.rx_hardwaregain_mode = 'slow_attack'

    print(f"Succès ! Fréquence actuelle : {sdr.rx_lo / 1e6} MHz")

    # 2. Capture
    samples = sdr.rx()

    # 3. Affichage du Spectre
    psd = np.abs(np.fft.fftshift(np.fft.fft(samples)))
    psd_dB = 10 * np.log10(psd**2 / len(psd))
    f = np.linspace(-sdr.sample_rate/2, sdr.sample_rate/2, len(psd))

    plt.figure(figsize=(10, 5))
    plt.plot((sdr.rx_lo + f) / 1e6, psd_dB, color='red')
    plt.title(f"Spectre FM à {sdr.rx_lo / 1e6} MHz (Pluto débridé)")
    plt.xlabel("Fréquence [MHz]")
    plt.ylabel("Puissance [dB]")
    plt.grid(True)
    plt.show()

except Exception as e:
    print(f"Erreur : {e}")
finally:
    del sdr