# HOMEMADE/READY/PlutoFMCW/fmcw_app.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys, os

# Imports locaux
sys.path.append(os.path.abspath("../../PlutoDoppler"))
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator
from fmcw_processor import FMCWProcessor

class FMCWRadarApp:
    def __init__(self):
        # --- PARAMÈTRES CONFIGURABLES ---
        self.fs, self.fc, self.n_samples, self.bw = 2_000_000, 2_100_000_000, 4096, 50_000_000
        self.tx_gain, self.rx_gain = -45, 30 # Gains optimisés pour éviter la saturation
        self.n_history = 100

        # --- INITIALISATION SDR ---
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = self.n_samples * 4
        self.hw.sdr.tx_hardwaregain_chan0 = self.tx_gain
        self.hw.set_rx_gain('manual', self.rx_gain)

        # Génération du signal de référence
        self.chirp_tx = SignalGenerator.generate_chirp(self.fs, self.n_samples, self.bw)
        self.hw.tx(self.chirp_tx)

        # --- INITIALISATION PROCESSEUR ---
        self.processor = FMCWProcessor(self.fs, self.bw, self.n_samples, self.chirp_tx)

        # --- INTERFACE GRAPHIQUE ---
        plt.style.use('dark_background')
        self.fig, (self.ax_spec, self.ax_water) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 1. Graphique du Spectre Instantané
        self.line_mti, = self.ax_spec.plot([], [], color='#ff0055', lw=2, label="Échos en mouvement (MTI)")
        self.ax_spec.set_ylim(-110, -50)
        self.ax_spec.set_xlim(0, 15)
        self.ax_spec.set_title("RADAR FMCW - SPECTRE DE DISTANCE", color='cyan', fontsize=14, pad=15)
        self.ax_spec.set_xlabel("Distance par rapport au capteur (mètres)", fontsize=10)
        self.ax_spec.set_ylabel("Puissance du signal (dBFS)", fontsize=10)
        self.ax_spec.grid(True, alpha=0.2, linestyle='--')
        self.ax_spec.legend(loc='upper right')

        # 2. Graphique Waterfall
        self.waterfall_data = np.full((self.n_history, self.n_samples // 2), -110.0)
        self.dist_max = (self.n_samples // 2) * self.processor.dist_res
        self.img = self.ax_water.imshow(self.waterfall_data, aspect='auto', cmap='magma',
                                        extent=[0, self.dist_max, self.n_history, 0],
                                        vmin=-105, vmax=-70)
        self.ax_water.set_title("HISTORIQUE DES DÉPLACEMENTS (WATERFALL)", color='orange', fontsize=12)
        self.ax_water.set_xlabel("Distance (mètres)", fontsize=10)
        self.ax_water.set_ylabel("Temps (Trames écoulées)", fontsize=10)
        self.ax_water.set_xlim(0, 15)

        # Interactions
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.fig, self.update, interval=30, blit=True, cache_frame_data=False)
        
        print(f"Radar FMCW prêt. Résolution : {self.processor.dist_res:.2f} m")
        plt.show()

    def update(self, frame):
        rx_data = self.hw.rx()
        dist_axis, psd_mti = self.processor.process_frame(rx_data)
        
        if dist_axis is None: return self.img, self.line_mti

        # Mise à jour Waterfall
        self.waterfall_data = np.roll(self.waterfall_data, -1, axis=0)
        self.waterfall_data[-1, :] = psd_mti
        self.img.set_array(self.waterfall_data)

        # Mise à jour Ligne
        self.line_mti.set_data(dist_axis, psd_mti)
        
        return self.img, self.line_mti

    def on_key(self, event):
        if event.key == 'r': 
            self.processor.reset_background()
            print(">>> Décor réinitialisé (Tare effectuée)")
        elif event.key == 'q': 
            plt.close()

if __name__ == "__main__":
    app = FMCWRadarApp()