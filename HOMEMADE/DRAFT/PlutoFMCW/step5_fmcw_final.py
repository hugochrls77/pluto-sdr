# HOMEMADE/DRAFT/PlutoFMCW/step5_fmcw_final.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys, os

sys.path.append(os.path.abspath("../../PlutoDoppler"))
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator

class PlutoFMCWWaterfall:
    def __init__(self):
        # 1. CONFIGURATION HD (50 MHz de BW pour 3m de résolution)
        self.fs, self.fc, self.n_samples, self.bw = 2_000_000, 2_100_000_000, 4096, 50_000_000
        self.n_history = 100 # Nombre de tranches temporelles affichées
        
        # 2. INITIALISATION MATÉRIELLE (Puissance augmentée)
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = self.n_samples * 4
        self.hw.sdr.tx_hardwaregain_chan0 = -70 # Puissance d'émission forte
        self.hw.set_rx_gain('manual', 10)       # Gain de réception très élevé

        self.chirp_tx = SignalGenerator.generate_chirp(self.fs, self.n_samples, self.bw)
        self.hw.tx(self.chirp_tx)

        # 3. MÉMOIRE ET WATERFALL
        self.background = None
        self.waterfall_data = np.full((self.n_history, self.n_samples // 2), -110.0)
        
        # 4. INTERFACE INSTRUMENTÉE
        plt.style.use('dark_background')
        self.fig, (self.ax_spec, self.ax_water) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Spectre instantané
        self.line_mti, = self.ax_spec.plot([], [], color='#ff0055', lw=2, label="Signal MTI")
        self.ax_spec.set_ylim(-110, -40)
        self.ax_spec.set_xlim(0, 15)
        self.ax_spec.set_title("SPECTRE DE DISTANCE INSTANTANÉ (MTI)", color='cyan')
        self.ax_spec.set_ylabel("Puissance (dBFS)")
        self.ax_spec.grid(True, alpha=0.2)

        # Waterfall (Temps vs Distance)
        self.dist_max = ( (self.n_samples//2) * 299792458 ) / (2 * self.bw)
        self.img = self.ax_water.imshow(self.waterfall_data, aspect='auto', cmap='magma',
                                        extent=[0, self.dist_max, self.n_history, 0],
                                        vmin=-105, vmax=-60)
        self.ax_water.set_title("HISTORIQUE DES DÉPLACEMENTS (WATERFALL)", color='orange')
        self.ax_water.set_xlabel("Distance (mètres)")
        self.ax_water.set_ylabel("Temps (Trames)")
        self.ax_water.set_xlim(0, 15) # On zoome sur les 15 premiers mètres

        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.fig, self.update, interval=50, blit=True)
        plt.show()

    def update(self, frame):
        rx_data = self.hw.rx()
        correlation = np.abs(np.correlate(rx_data, self.chirp_tx, mode='valid'))
        offset = np.argmax(correlation)
        rx_aligned = rx_data[offset : offset + self.n_samples]
        
        if len(rx_aligned) < self.n_samples: return self.img, self.line_mti

        # Dechirping & FFT
        beat_complex = rx_aligned * np.conj(self.chirp_tx)
        range_fft = np.fft.fft(beat_complex * np.blackman(self.n_samples))[:self.n_samples//2]

        # Traitement MTI (Soustraction Manuelle pour plus de sensibilité)
        if self.background is None: 
            self.background = range_fft
        else:
            self.background = self.background * 0.999 + range_fft * 0.001

        mti_complex = range_fft - self.background
        psd_mti = 20 * np.log10(np.abs(mti_complex) / self.n_samples + 1e-12)
        
        # Mise à jour Waterfall
        self.waterfall_data = np.roll(self.waterfall_data, -1, axis=0)
        self.waterfall_data[-1, :] = psd_mti
        self.img.set_array(self.waterfall_data)

        # Mise à jour Ligne
        dist_axis = np.arange(len(psd_mti)) * (299792458 / (2 * self.bw))
        self.line_mti.set_data(dist_axis, psd_mti)
        
        return self.img, self.line_mti

    def on_key(self, event):
        if event.key == 'r': 
            self.background = None # Capture un nouveau cliché de la pièce vide
            print("Background réinitialisé.")
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    PlutoFMCWWaterfall()