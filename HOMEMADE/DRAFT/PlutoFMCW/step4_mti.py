# HOMEMADE/DRAFT/PlutoFMCW/step4_mti.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys, os

sys.path.append(os.path.abspath("../../PlutoDoppler"))
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator

class PlutoFMCWMTI:
    def __init__(self):
        # 1. Configuration (Antennes branchées !)
        self.fs, self.fc, self.n_samples, self.bw = 2_000_000, 2_100_000_000, 4096, 20_000_000
        
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = self.n_samples * 4
        self.hw.sdr.tx_hardwaregain_chan0 = -15  # Puissance augmentée pour l'air
        self.hw.set_rx_gain('manual', 45)        # Gain plus fort pour les échos

        self.chirp_tx = SignalGenerator.generate_chirp(self.fs, self.n_samples, self.bw)
        self.hw.tx(self.chirp_tx)

        # 2. Mémoire MTI
        self.background = None # On stockera ici la "photo" de la pièce
        
        # 3. Interface
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.line_mti, = self.ax.plot([], [], color='#ff0055', lw=2, label="Signal MTI (Mouvement)")
        self.ax.set_ylim(-110, -40)
        self.ax.set_xlim(0, 30)
        self.ax.set_title("PHASE 4 : DÉTECTION DE MOUVEMENT (MTI)", color='cyan')
        self.ax.set_xlabel("Distance (mètres)", fontsize=10)
        self.ax.set_ylabel("Puissance (dBFS)", fontsize=10)
        self.ax.legend()

        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.fig, self.update, interval=50, blit=True)
        plt.show()

    def update(self, frame):
        rx_data = self.hw.rx()
        
        # Synchronisation
        correlation = np.abs(np.correlate(rx_data, self.chirp_tx, mode='valid'))
        offset = np.argmax(correlation)
        rx_aligned = rx_data[offset : offset + self.n_samples]
        
        if len(rx_aligned) < self.n_samples: return self.line_mti,

        # Dechirping (On reste en complexe pour la soustraction)
        beat_complex = rx_aligned * np.conj(self.chirp_tx)
        range_fft_complex = np.fft.fft(beat_complex * np.blackman(self.n_samples))[:self.n_samples//2]

        # --- LOGIQUE MTI ---
        if self.background is None:
            self.background = range_fft_complex # Capture de la pièce vide
            
        # Soustraction complexe (Annule les objets fixes)
        mti_complex = range_fft_complex - self.background
        psd_mti = 20 * np.log10(np.abs(mti_complex) / self.n_samples + 1e-12)
        
        # Mise à jour lente du décor (Optionnel, pour éviter de tout reset à la main)
        self.background = self.background * 0.98 + range_fft_complex * 0.02

        dist_axis = np.arange(len(psd_mti)) * (299792458 / (2 * self.bw))
        self.line_mti.set_data(dist_axis, psd_mti)
        return self.line_mti,

    def on_key(self, event):
        if event.key == 'r': self.background = None # Force le reset du décor
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    PlutoFMCWMTI()