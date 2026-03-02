# sdr_device.py
import adi
import numpy as np

class PlutoDevice:
    def __init__(self, ip="ip:192.168.2.1", fs=1_000_000, lo=5_800_000_000):
        print(f"[SDR] Initialisation du PlutoSDR à {lo/1e9:.2f} GHz...")
        self.sdr = adi.Pluto(ip)
        self.sdr.sample_rate = int(fs)
        
        # Configuration des oscillateurs
        self.sdr.rx_lo = int(lo)
        self.sdr.tx_lo = int(lo)
        
        # Bande passante matérielle
        self.sdr.rx_rf_bandwidth = int(fs)
        self.sdr.tx_rf_bandwidth = int(fs)
        
        # Réglage des gains
        self.sdr.tx_hardwaregain_chan0 = 0    # Gain max en émission (0 dB d'atténuation)
        self.sdr.rx_hardwaregain_chan0 = 40   # Gain RX élevé pour détecter les petites pales
        
    def transmit_cw(self):
        """Émet une porteuse continue pure (CW)."""
        # Un signal DC constant en bande de base génère une onde pure à la fréquence LO
        signal = np.ones(10000) * (2**14) + 1j * np.ones(10000) * (2**14)
        self.sdr.tx_cyclic_buffer = True
        self.sdr.tx(signal)
        print("[SDR] Transmission de l'onde continue en cours...")

    def receive_signal(self, num_samples):
        """Capture un bloc d'échantillons."""
        self.sdr.rx_buffer_size = int(num_samples)
        return self.sdr.rx()

    def stop(self):
        """Arrête la transmission et libère le matériel."""
        self.sdr.tx_destroy_buffer()
        print("[SDR] Transmission arrêtée.")