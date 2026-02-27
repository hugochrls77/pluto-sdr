import adi

class PlutoDevice:
    def __init__(self, ip="ip:192.168.2.1", fs=10_000_000, lo=900_000_000):
        print(f"[SDR] Initialisation du Pluto à {lo/1e6} MHz...")
        self.sdr = adi.Pluto(ip)
        self.sdr.sample_rate = int(fs)
        
        # Configuration des oscillateurs (Basse fréquence pour traverser les murs)
        self.sdr.rx_lo = int(lo)
        self.sdr.tx_lo = int(lo)
        
        # Bande passante matérielle
        self.sdr.rx_rf_bandwidth = int(fs)
        self.sdr.tx_rf_bandwidth = int(fs)
        
        # Gain
        self.sdr.tx_hardwaregain_chan0 = 0   # Gain TX max (attention, très puissant)
        self.sdr.rx_hardwaregain_chan0 = 40  # Gain RX modéré pour éviter la saturation par le mur
        
        self.fs = fs

    def transmit_signal(self, signal):
        self.sdr.tx_cyclic_buffer = True
        self.sdr.tx(signal)

    def receive_signal(self, num_samples):
        self.sdr.rx_buffer_size = num_samples
        return self.sdr.rx()

    def stop(self):
        self.sdr.tx_destroy_buffer()
        print("[SDR] Transmission arrêtée.")