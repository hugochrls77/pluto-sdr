import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator
from gui_manager import LabGUI
import time, re

class VelocityRadarStep3_2:
    def __init__(self):
        self.fs = 600_000 
        self.fc = 2_100_000_000 
        self.c = 299792458 
        self.lam = self.c / self.fc 
        
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = 65536 # Equilibre entre vitesse et précision
        
        # Accès registre gain (Méthode stable)
        self.rx_chan = self.hw.sdr._ctrl.find_channel("voltage0")
        self.rx_chan.attrs['gain_control_mode'].value = 'manual'
        self.current_gain = 45.0
        self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)
        
        self.ui = LabGUI(["1. SIGNAL TEMPOREL", "2. VITESSE HUMAINE (m/s)", "3. ÉTAT"])
        
        self.prev_rx = None
        self.psd_avg = None
        self.direction_flip = 1 # Changez en -1 si le sens est inversé

        self.hw.set_tx_gain(0)
        self.hw.tx(SignalGenerator.generate('Sinus', 0, self.fs, num_samples=10000))

        self.line_f, = self.ui.ax_f.plot([], [], '#00ff41', lw=1.5)
        self.ui.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.ui.fig, self.update, interval=100, cache_frame_data=False)
        plt.show()

    def update(self, frame):
        rx = self.hw.rx()
        
        # MTI
        if self.prev_rx is not None:
            rx_proc = rx - self.prev_rx
        else:
            rx_proc = rx
        self.prev_rx = rx.copy()

        # FFT avec Fenêtrage (pour éviter les bavures du 0 Hz)
        n = len(rx_proc)
        window = np.blackman(n)
        f_hz = np.fft.fftshift(np.fft.fftfreq(n, 1/self.fs))
        
        # Calcul de la vitesse avec correction de direction
        v_ms = self.direction_flip * (f_hz * self.lam) / 2
        
        psd = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx_proc * window))/n + 1e-12))
        
        if self.psd_avg is None: self.psd_avg = psd
        else: self.psd_avg = self.psd_avg * 0.4 + psd * 0.6

        # --- LOGIQUE DE DÉTECTION "HUMAINE" ---
        # On limite la recherche entre 0.2 m/s et 7.0 m/s uniquement
        # Cela élimine les parasites à 1500 m/s !
        search_mask = (np.abs(v_ms) > 0.2) & (np.abs(v_ms) < 7.0)
        
        if np.any(search_mask):
            idx_max = np.argmax(self.psd_avg[search_mask])
            detected_v = v_ms[search_mask][idx_max]
            detected_pwr = self.psd_avg[search_mask][idx_max]
        else:
            detected_v, detected_pwr = 0, -120

        # Mise à jour
        self.line_f.set_data(v_ms, self.psd_avg)
        self.ui.ax_f.set_xlim(-5, 5) # On ne regarde que la zone utile
        self.ui.ax_f.set_ylim(-110, -30)

        # Sidebar
        if detected_pwr > -85:
            sens = "APPROCHE" if detected_v > 0 else "ÉLOIGNE"
            speed_str = f"{abs(detected_v):.2f} m/s"
        else:
            sens = "---"
            speed_str = "0.00 m/s"

        self.ui.sidebar.set_text(f"--- RADAR V3.2 ---\n\n"
                                 f"SENS : {sens}\n"
                                 f"VITESSE : {speed_str}\n\n"
                                 f"Note: Si le sens est inversé,\n"
                                 f"appuyez sur 'D'.")

    def on_key(self, event):
        if event.key == 'd': # Touche pour inverser le sens de détection
            self.direction_flip *= -1
            print(f"Direction inversée (Multiplier: {self.direction_flip})")
        elif event.key == 'pageup':
            self.current_gain = min(71, self.current_gain + 2)
            self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)
        elif event.key == 'pagedown':
            self.current_gain = max(0, self.current_gain - 2)
            self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)

if __name__ == "__main__":
    VelocityRadarStep3_2()