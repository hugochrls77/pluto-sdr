import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator
from gui_manager import LabGUI

class PlutoDopplerRadar:
    def __init__(self):
        self.fs = 1_000_000 
        self.fc = 2_450_000_000 # Fréquence porteuse (2.45 GHz)
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = 16384 
        
        # GUI : 1. Vitesse/Temps | 2. Spectre | 3. Waterfall
        self.ui = LabGUI(["1. VITESSE (m/s) vs TEMPS", "2. SPECTRE DOPPLER", "3. WATERFALL"])
        
        self.zx = [1.0, 100.0, 1.0] 
        self.zy = [2.0, 100.0, 1.0] # Axe Y du graph 1 : +- 2 m/s
        
        # Historique pour le graphique 1D de vitesse
        self.v_history = np.zeros(100)
        self.t_axis = np.linspace(-5, 0, 100) # 5 dernières secondes
        
        # Données Waterfall
        self.wf_data = np.full((50, 512), -100)
        
        # Initialisation émission
        self.hw.tx(SignalGenerator.generate('Sinus', 0, self.fs, num_samples=10000))
        self.hw.set_tx_gain(0)
        self.hw.set_rx_gain('manual', 45)

        # Tracés
        self.line_v, = self.ui.ax_t.plot(self.t_axis, self.v_history, '#00d4ff', lw=2)
        self.line_f, = self.ui.ax_f.plot([], [], '#00ff41', lw=1.5)
        # Point rouge pour marquer le pic sur le spectre
        self.peak_marker, = self.ui.ax_f.plot([], [], 'ro', ms=8, label="Main détectée")
        
        self.img_wf = self.ui.ax_i.imshow(self.wf_data, aspect='auto', cmap='magma', 
                                         vmin=-100, vmax=-40, interpolation='bilinear')
        
        self.ui.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.ui.fig, self.update, interval=30, cache_frame_data=False)
        plt.show()

    def update(self, frame):
        rx = self.hw.rx()
        rx_cal = rx - np.mean(rx) # Suppression du statique
        
        n = len(rx)
        f_hz = np.fft.fftshift(np.fft.fftfreq(n, 1/self.fs))
        psd = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx_cal))/n + 1e-10))
        
        # --- DÉTECTION DU PIC (LA MAIN) ---
        # On définit une zone d'exclusion autour de 0 Hz pour ne pas détecter le bruit résiduel
        mask = (np.abs(f_hz) > 10) & (np.abs(f_hz) < 2000) 
        threshold = -75 # Niveau minimal pour considérer que c'est un mouvement
        
        current_v = 0
        if np.max(psd[mask]) > threshold:
            idx_max = np.where(mask)[0][np.argmax(psd[mask])]
            freq_doppler = f_hz[idx_max]
            # Formule : v = (fd * c) / (2 * fc) | c = 3e8 m/s
            current_v = (freq_doppler * 3e8) / (2 * self.fc)
            self.peak_marker.set_data([freq_doppler], [psd[idx_max]])
        else:
            self.peak_marker.set_data([], [])

        # --- MISE À JOUR DES GRAPHES ---
        # 1. Courbe de vitesse (1D)
        self.v_history = np.roll(self.v_history, -1)
        self.v_history[-1] = current_v
        self.line_v.set_ydata(self.v_history)
        self.ui.ax_t.set_ylim(-self.zy[0], self.zy[0])

        # 2. Spectre
        self.line_f.set_data(f_hz, psd)
        span = (self.fs / 2) / self.zx[1]
        self.ui.ax_f.set_xlim(-span, span)

        # 3. Waterfall
        mid = n // 2
        self.wf_data = np.roll(self.wf_data, -1, axis=0)
        self.wf_data[-1, :] = psd[mid-256 : mid+256]
        self.img_wf.set_array(self.wf_data)

        self.ui.sidebar.set_text(f"--- RADAR DE VITESSE ---\n\n"
                                 f"VITESSE : {current_v:+.2f} m/s\n"
                                 f"DOPPLER : {current_v * 2 * self.fc / 3e8:+.1f} Hz\n\n"
                                 f"Approcher : V > 0 (+)\n"
                                 f"Reculer   : V < 0 (-)")

    def on_key(self, event):
        if event.key == 'q': plt.close()
        elif event.key == 'r': self.v_history.fill(0); self.wf_data.fill(-100)

if __name__ == "__main__":
    PlutoDopplerRadar()