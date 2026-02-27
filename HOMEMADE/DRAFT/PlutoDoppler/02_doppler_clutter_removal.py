import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator
from gui_manager import LabGUI
import time
import re # On ajoute les expressions régulières pour nettoyer le texte

class DopplerFinalStable:
    def __init__(self):
        self.fs = 600_000 
        self.fc = 2_100_000_000 
        self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
        self.hw.sdr.rx_buffer_size = 8192
        
        # ACCÈS DIRECT AU REGISTRE
        self.phy = self.hw.sdr._ctrl
        self.rx_chan = self.phy.find_channel("voltage0")
        
        self.rx_chan.attrs['gain_control_mode'].value = 'manual'
        time.sleep(0.1)
        self.current_gain = 30.0
        self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)
        
        self.ui = LabGUI(["1. SIGNAL (MTI DIFF)", "2. SPECTRE DOPPLER", "3. ÉTAT"])
        self.active_plot = 1
        self.zx = [1.0, 40.0, 1.0] 
        self.zy = [0.1, 130.0, 1.0]
        
        self.prev_rx = None
        self.psd_avg = None

        self.hw.set_tx_gain(0)
        self.hw.tx(SignalGenerator.generate('Sinus', 0, self.fs, num_samples=10000))

        self.line_i, = self.ui.ax_t.plot([], [], '#00d4ff', lw=0.8)
        self.line_f, = self.ui.ax_f.plot([], [], '#00ff41', lw=1.2)
        
        self.ui.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.ui.fig, self.update, interval=80, cache_frame_data=False)
        plt.show()

    def update(self, frame):
        # --- NETTOYAGE DU GAIN (Correction de l'erreur string to float) ---
        raw_val = self.rx_chan.attrs['hardwaregain'].value
        # On ne garde que les chiffres, le point et le signe moins
        clean_val = re.findall(r"[-+]?\d*\.\d+|\d+", raw_val)[0]
        real_g = float(clean_val)
        
        rx = self.hw.rx()
        
        if self.prev_rx is not None:
            rx_proc = rx - self.prev_rx
        else:
            rx_proc = rx
        self.prev_rx = rx.copy()

        n = len(rx_proc)
        f_hz = np.fft.fftshift(np.fft.fftfreq(n, 1/self.fs))
        psd_inst = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx_proc))/n + 1e-12))
        
        if self.psd_avg is None: self.psd_avg = psd_inst
        else: self.psd_avg = self.psd_avg * 0.7 + psd_inst * 0.3

        self.line_i.set_data(np.arange(n), rx_proc.real)
        self.ui.ax_t.set_ylim(-self.zy[0], self.zy[0])
        
        self.line_f.set_data(f_hz, self.psd_avg)
        span = (self.fs / 2) / self.zx[1]
        self.ui.ax_f.set_xlim(-span, span)
        self.ui.ax_f.set_ylim(-self.zy[1], -20)

        self.ui.sidebar.set_text(f"GAIN HW : {real_g:.1f} dB\n\n"
                                 f"STATUT : OK\n\n"
                                 f"Faites un mouvement\n"
                                 f"rapide pour voir\n"
                                 f"le pic Doppler.")

    def on_key(self, event):
        self.active_plot, self.zx, self.zy = self.ui.handle_interaction(event, self.active_plot, self.zx, self.zy)
        if event.key == 'pageup':
            self.current_gain = min(71, self.current_gain + 2)
            self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)
        elif event.key == 'pagedown':
            self.current_gain = max(0, self.current_gain - 2)
            self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)
        elif event.key == 'q':
            plt.close()

if __name__ == "__main__":
    DopplerFinalStable()