import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator
from gui_manager import LabGUI

class DopplerStep1:
    def __init__(self):
        self.fs = 1_000_000
        self.fc = 2_450_000_000
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = 32768 
        
        self.ui = LabGUI(["1. SIGNAL I/Q", "2. SPECTRE DOPPLER", "3. ÉTAT SYSTÈME"])
        
        # PARAMÈTRES DE CADRAGE (Identiques à tes screenshots préférés)
        self.active_plot = 1
        self.zx = [1.0, 100.0, 1.0] # Zoom X par défaut sur le spectre
        self.zy = [0.2, 110.0, 0.2] # Zoom Y pour voir les petits échos
        
        # Emission
        self.hw.set_tx_gain(-10)
        self.hw.tx(SignalGenerator.generate('Sinus', 0, self.fs, num_samples=10000))
        self.hw.set_rx_gain('manual', 45)

        self.line_i, = self.ui.ax_t.plot([], [], '#00d4ff', lw=0.8)
        self.line_f, = self.ui.ax_f.plot([], [], '#00ff41', lw=1)
        
        self.ui.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.ui.fig, self.update, interval=30, cache_frame_data=False)
        plt.show()

    def update(self, frame):
        rx = self.hw.rx()
        n = len(rx)
        
        t_ms = np.arange(n) / self.fs * 1000
        f_hz = np.fft.fftshift(np.fft.fftfreq(n, 1/self.fs))
        psd = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx))/n + 1e-12))
        
        # Mise à jour du focus visuel
        self.ui.update_focus(self.active_plot)

        # Tracés avec application des zooms dynamiques
        self.line_i.set_data(t_ms, rx.real)
        self.ui.ax_t.set_xlim(0, t_ms[-1] / self.zx[0])
        self.ui.ax_t.set_ylim(-self.zy[0], self.zy[0])

        self.line_f.set_data(f_hz, psd)
        span = (self.fs / 2) / self.zx[1]
        self.ui.ax_f.set_xlim(-span, span)
        self.ui.ax_f.set_ylim(-self.zy[1], -10)

        self.ui.sidebar.set_text(
            f"--- RADAR : BASELINE ---\n\n"
            f"GAIN RX : {self.hw.rx_gain} dB\n"
            f"ZOOM SPECTRE : x{self.zx[1]:.0f}\n\n"
            f"COMMANDES :\n"
            f" [1,2,3] : Focus\n"
            f" [+/-]   : Zoom X\n"
            f" [UP/DN] : Zoom Y\n"
            f" [PgUp/Dn]: Gain Hardware"
        )

    def on_key(self, event):
        # 1. Gestion interactive (Zoom/Focus) via la GUI
        self.active_plot, self.zx, self.zy = self.ui.handle_interaction(
            event, self.active_plot, self.zx, self.zy
        )
        
        # 2. Gestion Hardware (Spécifique au script)
        if event.key == 'pageup':
            self.hw.set_rx_gain('manual', self.hw.rx_gain + 2)
        elif event.key == 'pagedown':
            self.hw.set_rx_gain('manual', self.hw.rx_gain - 2)
        elif event.key == 'q':
            plt.close()

if __name__ == "__main__":
    DopplerStep1()