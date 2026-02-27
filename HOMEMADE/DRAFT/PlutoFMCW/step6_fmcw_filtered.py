# HOMEMADE/DRAFT/PlutoFMCW/step6_fmcw_filtered.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys, os

# Accès aux modules de base du dossier parent
sys.path.append(os.path.abspath("../../PlutoDoppler"))
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator

class PlutoFMCWFiltered:
    def __init__(self):
        # 1. CONFIGURATION (50 MHz de BW = Résolution de 3 mètres)
        self.fs = 2_000_000
        self.fc = 2_100_000_000
        self.n_samples = 4096
        self.bw = 50_000_000 #
        self.n_history = 100 
        
        # 2. INITIALISATION MATÉRIELLE (Gains bas pour éviter la saturation)
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = self.n_samples * 4
        # Gains réduits suite aux tests de saturation
        self.hw.sdr.tx_hardwaregain_chan0 = -40 
        self.hw.set_rx_gain('manual', 35)       

        # Génération du Chirp
        self.chirp_tx = SignalGenerator.generate_chirp(self.fs, self.n_samples, self.bw)
        self.hw.tx(self.chirp_tx)

        # 3. MÉMOIRE ET WATERFALL
        self.background = None
        self.waterfall_data = np.full((self.n_history, self.n_samples // 2), -110.0)
        
        # 4. INTERFACE GRAPHIQUE INSTRUMENTÉE
        plt.style.use('dark_background')
        self.fig, (self.ax_spec, self.ax_water) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Graphique du Spectre instantané
        self.line_mti, = self.ax_spec.plot([], [], color='#ff0055', lw=2, label="Signal MTI (Filtré)")
        self.ax_spec.set_ylim(-110, -50)
        self.ax_spec.set_xlim(0, 15) # On surveille les 15 premiers mètres
        self.ax_spec.set_title("SPECTRE DE DISTANCE AVEC FILTRE ANTI-FUITE", color='cyan', fontsize=12)
        self.ax_spec.set_xlabel("Distance (mètres)", fontsize=10)
        self.ax_spec.set_ylabel("Puissance (dBFS)", fontsize=10)
        self.ax_spec.grid(True, alpha=0.2)
        self.ax_spec.legend(loc='upper right')

        # Graphique Waterfall (Historique)
        self.dist_max = ( (self.n_samples//2) * 299792458 ) / (2 * self.bw)
        self.img = self.ax_water.imshow(self.waterfall_data, aspect='auto', cmap='magma',
                                        extent=[0, self.dist_max, self.n_history, 0],
                                        vmin=-105, vmax=-70)
        self.ax_water.set_title("HISTORIQUE TEMPS / DISTANCE", color='orange', fontsize=12)
        self.ax_water.set_xlabel("Distance (mètres)", fontsize=10)
        self.ax_water.set_ylabel("Temps (Trames)", fontsize=10)
        self.ax_water.set_xlim(0, 15)

        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.fig, self.update, interval=50, blit=True, cache_frame_data=False)
        plt.show()

    def update(self, frame):
        rx_data = self.hw.rx()
        
        # Synchronisation par corrélation croisée
        correlation = np.abs(np.correlate(rx_data, self.chirp_tx, mode='valid'))
        offset = np.argmax(correlation)
        rx_aligned = rx_data[offset : offset + self.n_samples]
        
        if len(rx_aligned) < self.n_samples: 
            return self.img, self.line_mti

        # --- TRAITEMENT RADAR ---
        # 1. Dechirping
        beat_complex = rx_aligned * np.conj(self.chirp_tx)

        # 2. FILTRE PASSE-HAUT (Suppression du pic à 0m / DC Offset)
        # On retire la moyenne pour "tuer" la fuite directe entre antennes
        beat_complex -= np.mean(beat_complex) 

        # 3. FFT (Transformation Fréquence -> Distance)
        range_fft = np.fft.fft(beat_complex * np.blackman(self.n_samples))[:self.n_samples//2]

        # 4. SOUSTRACTION DYNAMIQUE (MTI)
        if self.background is None: 
            self.background = range_fft
        else:
            # Apprentissage très lent du décor (0.1% par trame)
            self.background = self.background * 0.999 + range_fft * 0.001
            
        mti_complex = range_fft - self.background
        psd_mti = 20 * np.log10(np.abs(mti_complex) / self.n_samples + 1e-12)
        
        # 5. MISE À JOUR DU WATERFALL
        self.waterfall_data = np.roll(self.waterfall_data, -1, axis=0)
        self.waterfall_data[-1, :] = psd_mti
        self.img.set_array(self.waterfall_data)

        # 6. MISE À JOUR DE LA LIGNE
        dist_axis = np.arange(len(psd_mti)) * (299792458 / (2 * self.bw))
        self.line_mti.set_data(dist_axis, psd_mti)
        
        return self.img, self.line_mti

    def on_key(self, event):
        if event.key == 'r': 
            self.background = None 
            print("Décor réinitialisé.")
        elif event.key == 'q': 
            plt.close()

if __name__ == "__main__":
    PlutoFMCWFiltered()