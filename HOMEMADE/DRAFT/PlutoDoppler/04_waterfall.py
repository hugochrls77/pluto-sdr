import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import re, time

# Import de tes modules perso
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator

class MasterRadarFinal:
    def __init__(self):
        # --- 1. CONFIGURATION MATÉRIELLE ---
        self.fs = 600_000 
        self.fc = 2_100_000_000 
        self.lam = 299792458 / self.fc
        
        try:
            self.hw = PlutoDevice(fs=self.fs, lo=self.fc)
            self.hw.sdr.rx_buffer_size = 65536 # Compromis fluidité/précision
            self.rx_chan = self.hw.sdr._ctrl.find_channel("voltage0")
            self.rx_chan.attrs['gain_control_mode'].value = 'manual'
            self.current_gain = 45.0
            self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)
        except Exception as e:
            print(f"Erreur Pluto : {e}")
            return

        # --- 2. LOGIQUE RADAR ---
        self.direction_flip = 1 
        self.squelch_level = -95
        self.n_history = 120
        self.v_limit = 4.0
        self.hz_limit = 5000
        
        self.data_hz = np.full((self.n_history, 400), -115.0)
        self.data_ms = np.full((self.n_history, 400), -115.0)
        self.prev_rx = None

        # --- 3. INTERFACE GRAPHIQUE (UI) ---
        plt.style.use('dark_background')
        self.fig, (self.ax_hz, self.ax_ms) = plt.subplots(2, 1, figsize=(12, 10))
        self.fig.canvas.manager.set_window_title("RADAR DOPPLER PROFESSIONNEL - MASTER V5.5")

        # Configuration Vue Fréquences (Hz)
        self.img_hz = self.ax_hz.imshow(self.data_hz, aspect='auto', animated=True,
                                       extent=[-self.hz_limit, self.hz_limit, 0, self.n_history],
                                       cmap='viridis', vmin=-100, vmax=-55)
        self.ax_hz.set_title("ANALYSE TECHNIQUE (Hz)", color='cyan', fontsize=12, loc='left')
        self.ax_hz.set_ylabel("Historique (Frames)")
        self.ax_hz.grid(True, alpha=0.1)

        # Configuration Vue Vitesse (m/s)
        self.img_ms = self.ax_ms.imshow(self.data_ms, aspect='auto', animated=True,
                                       extent=[-self.v_limit, self.v_limit, 0, self.n_history],
                                       cmap='magma', vmin=-100, vmax=-45)
        self.ax_ms.set_title("MESURE DE VITESSE (m/s)", color='orange', fontsize=12, loc='left')
        self.ax_ms.set_xlabel("Vitesse (m/s)  [ < ÉLOIGNE | APPROCHE > ]", fontsize=10)
        self.ax_ms.axvline(0, color='white', alpha=0.3, ls='--')

        # Statut text (attaché à l'axe pour éviter le bug de blitting)
        self.txt = self.ax_hz.text(0.01, 0.95, "", transform=self.ax_hz.transAxes, 
                                  color='#00ff41', family='monospace', fontsize=9,
                                  bbox=dict(facecolor='black', alpha=0.7))

        # Émission
        self.hw.set_tx_gain(0)
        self.hw.tx(SignalGenerator.generate('Sinus', 0, self.fs, num_samples=10000))

        self.fig.tight_layout()
        self.ani = FuncAnimation(self.fig, self.update, interval=40, blit=True, cache_frame_data=False)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        plt.show()

    def update(self, frame):
        # 1. Acquisition et MTI
        rx = self.hw.rx()
        if self.prev_rx is not None: rx_proc = rx - self.prev_rx
        else: rx_proc = rx
        self.prev_rx = rx.copy()

        # 2. Calculs FFT
        n = len(rx)
        window = np.hanning(n)
        f_hz = np.fft.fftshift(np.fft.fftfreq(n, 1/self.fs))
        v_ms = self.direction_flip * (f_hz * self.lam) / 2
        
        psd_raw = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx * window))/n + 1e-12))
        psd_mti = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx_proc * window))/n + 1e-12))

        # 3. Mise à jour Image Hz
        mask_hz = (f_hz >= -self.hz_limit) & (f_hz <= self.hz_limit)
        res_hz = np.interp(np.linspace(-self.hz_limit, self.hz_limit, 400), f_hz[mask_hz], psd_raw[mask_hz])
        self.data_hz = np.roll(self.data_hz, -1, axis=0)
        self.data_hz[-1, :] = res_hz
        self.img_hz.set_array(self.data_hz)

        # 4. Mise à jour Image m/s
        mask_v = (v_ms >= -self.v_limit) & (v_ms <= self.v_limit)
        res_v = np.interp(np.linspace(-self.v_limit, self.v_limit, 400), v_ms[mask_v], psd_mti[mask_v])
        
        # Post-traitement (Zone morte + Squelch)
        res_v[194:206] = -115.0 
        res_v[res_v < self.squelch_level] = -115.0
        
        self.data_ms = np.roll(self.data_ms, -1, axis=0)
        self.data_ms[-1, :] = res_v
        self.img_ms.set_array(self.data_ms)

        # 5. Calcul Vitesse Max pour Sidebar
        search_mask = (np.abs(v_ms) > 0.2) & (np.abs(v_ms) < 6.0)
        idx_max = np.argmax(psd_mti[search_mask])
        v_max = abs(v_ms[search_mask][idx_max]) if psd_mti[search_mask][idx_max] > self.squelch_level else 0

        self.txt.set_text(f"GAIN: {self.current_gain}dB | SQL: {self.squelch_level}dB | V_MAX: {v_max:.2f}m/s")
        return self.img_hz, self.img_ms, self.txt

    def on_key(self, event):
        if event.key == 'd': self.direction_flip *= -1
        elif event.key == 'pageup':
            self.current_gain = min(71, self.current_gain + 2)
            self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)
        elif event.key == 'pagedown':
            self.current_gain = max(0, self.current_gain - 2)
            self.rx_chan.attrs['hardwaregain'].value = str(self.current_gain)
        elif event.key == '+': self.squelch_level -= 2
        elif event.key == '-': self.squelch_level += 2
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    MasterRadarFinal()