# HOMEMADE/READY/PlutoFMCW/fmcw_processor.py
import numpy as np

class FMCWProcessor:
    def __init__(self, fs, bw, n_samples, chirp_tx):
        self.fs = fs
        self.bw = bw
        self.n_samples = n_samples
        self.chirp_tx = chirp_tx
        self.background = None
        self.mti_alpha = 0.001 # Vitesse d'apprentissage du décor (0.1%)
        
        # Prévu pour la conversion Distance : c / (2 * BW)
        self.dist_res = 299792458 / (2 * self.bw)

    def process_frame(self, rx_data):
        """Chaîne complète : Synchro -> Dechirp -> MTI -> PSD"""
        # 1. Synchronisation par corrélation
        correlation = np.abs(np.correlate(rx_data, self.chirp_tx, mode='valid'))
        offset = np.argmax(correlation)
        rx_aligned = rx_data[offset : offset + self.n_samples]
        
        if len(rx_aligned) < self.n_samples:
            return None, None

        # 2. Dechirping (Mélangeur)
        beat_complex = rx_aligned * np.conj(self.chirp_tx)
        
        # 3. FFT avec Fenêtrage Blackman
        range_fft = np.fft.fft(beat_complex * np.blackman(self.n_samples))[:self.n_samples//2]

        # 4. Traitement MTI (Soustraction de Background)
        if self.background is None:
            self.background = range_fft
        else:
            # Mise à jour lente du décor
            self.background = self.background * (1 - self.mti_alpha) + range_fft * self.mti_alpha
            
        mti_complex = range_fft - self.background
        
        # 5. Conversion en dBFS
        psd_mti = 20 * np.log10(np.abs(mti_complex) / self.n_samples + 1e-12)
        
        # Axe des distances
        dist_axis = np.arange(len(psd_mti)) * self.dist_res
        
        return dist_axis, psd_mti

    def reset_background(self):
        self.background = None