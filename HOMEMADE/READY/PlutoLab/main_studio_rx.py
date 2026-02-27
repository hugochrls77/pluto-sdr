import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sdr_device import PlutoDevice
from gui_manager import LabGUI

class PlutoWifiScanner:
    def __init__(self):
        # 1. CONFIGURATION ANTENNE (WiFi Canal 1 : 2.412 GHz)
        self.fs = 20_000_000  # 20 MHz pour voir tout le canal
        self.hw = PlutoDevice(fs=self.fs, lo=2_412_000_000)
        
        # On utilise notre GUI habituelle
        self.ui = LabGUI(["1. BURSTS TEMPORELS", "2. SPECTRE WIFI (2.4 GHz)", "3. ACTIVITÉ I/Q"])
        
        self.active_plot = 1 # Focus sur le spectre par défaut
        self.paused = False
        self.peak_enabled = True
        
        # Réglages de zoom pour l'antenne
        self.zx = [1.0, 1.0, 1.0]
        self.zy = [0.2, 90.0, 0.2] # On zoom bcp plus (les signaux d'antenne sont faibles)
        
        self.peak_f = None

        # --- INITIALISATION DES LIGNES ---
        self.line_rx, = self.ui.ax_t.plot([], [], '#00d4ff', lw=0.5)
        self.line_f, = self.ui.ax_f.plot([], [], '#ff0055', lw=1)
        self.line_p, = self.ui.ax_f.plot([], [], '#ffaa00', lw=0.8, alpha=0.3)
        self.line_iq, = self.ui.ax_i.plot([], [], 'o', color='#00d4ff', ms=1, alpha=0.1)

        # On s'assure que le TX est bien éteint
        self.hw.stop_tx()
        
        self.ui.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.ui.fig, self.update, interval=30, cache_frame_data=False)
        plt.show()

    def update(self, frame):
        if self.paused: return
        
        # 1. ACQUISITION
        rx = self.hw.rx()
        
        # 2. CALCUL SPECTRE (Frequence absolue en MHz)
        # On centre l'axe sur la fréquence de réception (ex: 2412 MHz)
        f_mhz = (np.fft.fftshift(np.fft.fftfreq(len(rx), 1/self.fs)) + self.hw.sdr.rx_lo) / 1e6
        psd = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx))/len(rx)+1e-6))
        
        # Logic Peak Hold (Indispensable pour le WiFi qui est intermittent !)
        if self.peak_enabled:
            if self.peak_f is None or len(self.peak_f) != len(psd): self.peak_f = psd
            else: self.peak_f = np.maximum(self.peak_f, psd)
            self.line_p.set_data(f_mhz, self.peak_f)
        else:
            self.line_p.set_data([], [])

        # 3. MISE À JOUR DES TRACÉS
        t_us = np.arange(len(rx)) / (self.fs / 1e6) # Temps en microsecondes
        self.line_rx.set_data(t_us, rx.real)
        self.ui.ax_t.set_xlim(0, t_us[-1] / self.zx[0]); self.ui.ax_t.set_ylim(-self.zy[0], self.zy[0])

        self.line_f.set_data(f_mhz, psd)
        self.ui.ax_f.set_xlim(f_mhz[0], f_mhz[-1]); self.ui.ax_f.set_ylim(-self.zy[1], 0)

        self.line_iq.set_data(rx.real, rx.imag)
        self.ui.ax_i.set_xlim(-self.zy[2], self.zy[2]); self.ui.ax_i.set_ylim(-self.zy[2], self.zy[2])

        # 4. SIDEBAR
        mode = self.hw.sdr.rx_gain_control_mode_chan0
        self.ui.sidebar.set_text(
            f"--- ANTENNA SCANNER ---\n"
            f"FREQ : {self.hw.sdr.rx_lo/1e6:.1f} MHz\n\n"
            f" [←/→] : Scan Canal (5MHz)\n"
            f" [PgUp/Dn] : Gain ({mode})\n"
            f" [A] : Mode AGC\n"
            f" [P] : Peak Hold\n"
            f" [R] : Reset Peak\n\n"
            f" [Q] : Quitter"
        )

    def on_key(self, event):
        if event.key == 'right': 
            self.hw.set_lo(self.hw.sdr.rx_lo + 5_000_000)
            self.peak_f = None
        elif event.key == 'left': 
            self.hw.set_lo(self.hw.sdr.rx_lo - 5_000_000)
            self.peak_f = None
        elif event.key == 'up': self.zy[self.active_plot] *= 0.8
        elif event.key == 'down': self.zy[self.active_plot] *= 1.2
        elif event.key == 'pageup': self.hw.set_rx_gain('manual', min(73, self.hw.rx_gain+2))
        elif event.key == 'pagedown': self.hw.set_rx_gain('manual', max(0, self.hw.rx_gain-2))
        elif event.key == 'a': self.hw.set_rx_gain('slow_attack')
        elif event.key == 'p': self.peak_enabled = not self.peak_enabled
        elif event.key == 'r': self.peak_f = None
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    PlutoWifiScanner()