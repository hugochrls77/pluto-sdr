# HOMEMADE/DRAFT/PlutoFMCW/main_fmcw_mti.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys, os

sys.path.append(os.path.abspath("../../PlutoDoppler"))
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator

class PlutoFMCWMTI:
    def __init__(self):
        self.fs, self.fc, self.bw, self.n_fft = 2_000_000, 2_100_000_000, 40_000_000, 8192
        
        # --- CONFIGURATION ANTENNES ---
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = self.n_fft * 2
        # On augmente la puissance pour l'air (Attention : ne plus brancher le câble !)
        self.hw.sdr.tx_hardwaregain_chan0 = -10 
        self.hw.set_rx_gain('manual', 50) # Gain RX élevé pour les échos lointains
        
        self.chirp_tx = SignalGenerator.generate_chirp(self.fs, self.n_fft, self.bw)
        self.hw.tx(self.chirp_tx)
        
        # --- MÉMOIRE POUR MTI ---
        self.background = None # Stocke l'image de la pièce vide
        self.zero_offset = 142.0 # À ajuster selon ta valeur trouvée au test câble
        
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.line, = self.ax.plot([], [], color='#00ff41', lw=1.5, label="Signal Temps Réel")
        self.line_mti, = self.ax.plot([], [], color='#ff0055', lw=2, label="Détection de Mouvement (MTI)")
        
        self.ax.set_ylim(-110, -30)
        self.ax.set_xlim(-2, 15) # On regarde les 15 premiers mètres
        self.ax.legend()
        self.ax.set_title("RADAR FMCW - DÉTECTION DE MOUVEMENT", color='cyan')

        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.fig, self.update, interval=50, blit=True)
        plt.show()

    def update(self, frame):
        rx = self.hw.rx()
        correlation = np.abs(np.correlate(rx, self.chirp_tx, mode='valid'))
        offset = np.argmax(correlation)
        rx_aligned = rx[offset : offset + self.n_fft]
        
        if len(rx_aligned) < self.n_fft: return self.line, self.line_mti

        # Dechirping & FFT (on travaille en complexe pour le MTI)
        mixed = rx_aligned * np.conj(self.chirp_tx)
        range_fft_complex = np.fft.fft(mixed * np.blackman(self.n_fft))[:self.n_fft//2]
        
        # 1. Signal Brut (en dB)
        psd_raw = 20 * np.log10(np.abs(range_fft_complex) / self.n_fft + 1e-12)
        
        # 2. TRAITEMENT MTI (Soustraction du Background)
        if self.background is None:
            self.background = range_fft_complex # Initialisation
            
        # On soustrait le background complexe (supprime la phase fixe de la fuite directe)
        mti_signal = range_fft_complex - self.background
        psd_mti = 20 * np.log10(np.abs(mti_signal) / self.n_fft + 1e-12)
        
        # Mise à jour lente du background (pour s'adapter aux changements de la pièce)
        self.background = self.background * 0.95 + range_fft_complex * 0.05
        
        dist_axis = np.arange(len(psd_raw)) * (299792458 / (2 * self.bw)) - self.zero_offset

        self.line.set_data(dist_axis, psd_raw)
        self.line_mti.set_data(dist_axis, psd_mti)
        return self.line, self.line_mti

    def on_key(self, event):
        if event.key == 'r': self.background = None # Reset le décor
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    PlutoFMCWMTI()