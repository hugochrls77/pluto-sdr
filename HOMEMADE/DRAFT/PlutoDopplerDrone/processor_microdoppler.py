# processor_microdoppler.py
import numpy as np

class MicroDopplerProcessor:
    def __init__(self, nfft, decimation, mti_alpha):
        self.nfft = nfft
        self.decimation = decimation
        self.mti_alpha = mti_alpha
        self.slow_background = None

    def process_stft(self, rx_signal):
        """Prend le signal brut, décime, filtre et sort un profil de vitesse."""
        
        # 1. DÉCIMATION : Le secret pour voir les pales !
        # On ne garde qu'un échantillon sur N pour observer les mouvements lents/moyens
        rx_decimated = rx_signal[::self.decimation]
        
        # 2. FILTRE MTI (Annulation du couplage TX/RX et objets fixes)
        # On calcule la moyenne de la trame (qui représente les objets à 0 Hz)
        current_mean = np.mean(rx_decimated)
        
        if self.slow_background is None:
            self.slow_background = current_mean
            
        # Lissage exponentiel de l'empreinte statique
        self.slow_background = (1 - self.mti_alpha) * self.slow_background + self.mti_alpha * current_mean
        
        # Soustraction pour isoler la dynamique
        dynamic_signal = rx_decimated - self.slow_background
        
        # 3. TRANSFORMÉE DE FOURIER (STFT)
        # Fenêtrage pour éviter les artefacts de bords
        window = np.hanning(len(dynamic_signal))
        # On peut rajouter du 'zero-padding' si dynamic_signal est plus court que NFFT
        spectrum = np.fft.fftshift(np.fft.fft(dynamic_signal * window, n=self.nfft))
        
        # 4. PUISSANCE LOGARITHMIQUE (dB)
        magnitude_db = 20 * np.log10(np.abs(spectrum) + 1e-10)
        return magnitude_db