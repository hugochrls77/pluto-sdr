import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator
from gui_manager import LabGUI

class PlutoFMCWRadar:
    def __init__(self):
        self.fs = 50_000_000 # On pousse le Pluto à 50 MHz de bande
        self.fc = 2_000_000_000 # Centre à 2 GHz (entre 1.5 et 2.5)
        self.bw = 40_000_000 # Balayage de 40 MHz
        
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = 32768
        
        self.ui = LabGUI(["1. ECHO (DECHIRPED)", "2. DISTANCE (FFT)", "3. WATERFALL DISTANCE"])
        
        # Génération du Chirp de référence
        self.chirp_tx = SignalGenerator.generate_chirp(self.fs, 32768, self.bw)
        self.hw.tx(self.chirp_tx)
        
        self.hw.set_tx_gain(0)
        self.hw.set_rx_gain('manual', 50)

        # Tracés
        self.line_r, = self.ui.ax_f.plot([], [], '#ff0055', lw=1.5)
        self.img_wf = self.ui.ax_i.imshow(np.full((50, 256), -100), aspect='auto', 
                                         cmap='viridis', extent=[0, 100, 0, 50])
        
        self.ui.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.ui.fig, self.update, interval=30, cache_frame_data=False)
        plt.show()

    def update(self, frame):
        rx = self.hw.rx()
        
        # --- LOGIQUE FMCW (DECHIRPING) ---
        # On multiplie le reçu par le conjugué de l'émis pour extraire la diff de fréquence
        # f_beat = (SDR_delay + Distance_delay) * (BW / T_chirp)
        mixed = rx * np.conj(self.chirp_tx[:len(rx)])
        
        # FFT du signal mélangé = Spectre des distances
        n = len(mixed)
        range_fft = np.abs(np.fft.fft(mixed))[:n//2]
        range_db = 20*np.log10(range_fft / n + 1e-6)
        
        # Axe distance (approximatif car la latence USB est dominante)
        # 1 bin FFT ~ (c / (2 * BW))
        dist_axis = np.arange(len(range_db)) * (3e8 / (2 * self.bw))

        # --- AFFICHAGE ---
        self.line_r.set_data(dist_axis, range_db)
        self.ui.ax_f.set_xlim(0, 50) # On regarde les 50 premiers mètres
        self.ui.ax_f.set_ylim(-100, -20)
        
        self.ui.sidebar.set_text(f"--- RADAR FMCW ---\n"
                                 f"Bande : {self.bw/1e6} MHz\n"
                                 f"Centre : {self.fc/1e9} GHz\n\n"
                                 f"Le pic à 0m est la fuite TX.\n"
                                 f"Un mouvement de main fera\n"
                                 f"osciller les pics suivants.")

    def on_key(self, event):
        if event.key == 'q': plt.close()

if __name__ == "__main__":
    PlutoFMCWRadar()