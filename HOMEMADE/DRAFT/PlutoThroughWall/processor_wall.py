import numpy as np

class WallProcessor:
    def __init__(self, nfft=2048):
        self.nfft = nfft
        self.mti_alpha = 0.05           
        self.slow_background = None     # Empreinte complexe

    def process_fmcw_aligned(self, tx_signal, rx_signal):
        """Mélange, FFT, et ALIGNEMENT DE PHASE (Méthode par autocorrélation indirecte)"""
        min_len = min(len(tx_signal), len(rx_signal))
        tx = tx_signal[:min_len]
        rx = rx_signal[:min_len]
        
        # 1. Mixage classique FMCW
        mixed = rx * np.conj(tx)
        
        # 2. FFT Complexe
        window = np.hanning(len(mixed))
        range_profile = np.fft.fft(mixed * window, self.nfft)
        
        # On ne garde que les distances réelles (fréquences positives)
        profile_pos = range_profile[:self.nfft//2]
        
        # 3. LE SECRET (L'équivalent de leur autocorrélation) : Alignement de la phase
        # On trouve le pic statique dominant (le mur ou la fuite d'antenne directe)
        reference_peak_idx = np.argmax(np.abs(profile_pos))
        
        # On extrait la phase de ce pic (qui contient le "jitter" matériel aléatoire du Pluto)
        reference_phase = np.angle(profile_pos[reference_peak_idx])
        
        # On "détourne" l'ensemble du profil pour annuler l'erreur de phase
        # En multipliant par l'exponentielle complexe inverse
        aligned_profile = profile_pos * np.exp(-1j * reference_phase)
        
        return aligned_profile

    def calibrate(self, profiles):
        """Prend l'empreinte parfaite avec des phases stabilisées"""
        self.slow_background = np.mean(profiles, axis=0)
        print("[TRAITEMENT] Empreinte complexe stabilisée enregistrée !")

    def get_dynamic_signal(self, current_profile):
        """Soustraction VECTORIELLE (complexe) du mur"""
        if self.slow_background is None:
            return np.abs(current_profile)
        
        # Mise à jour lente de l'empreinte (MTI)
        self.slow_background = (1 - self.mti_alpha) * self.slow_background + self.mti_alpha * current_profile
        
        # 4. Soustraction Complexe
        # La phase du SDR étant verrouillée, on peut soustraire les complexes sans créer de bandes !
        dynamic_complex = current_profile - self.slow_background
        
        # On retourne l'amplitude pour l'affichage graphique
        return np.abs(dynamic_complex)