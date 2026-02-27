import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import adi

# Style Dark Lab Pro
plt.style.use('dark_background')
plt.rcParams['font.family'] = 'monospace'
plt.rcParams['keymap.save'] = '' 

class PlutoLoopbackFinalPro:
    def __init__(self, ip="ip:192.168.2.1"):
        try:
            self.sdr = adi.Pluto(ip)
            self.fs = 2_000_000 # 2 MHz idéal pour le câble
            self.sdr.sample_rate = self.fs
            self.sdr.rx_lo = self.sdr.tx_lo = 800_000_000
            
            # --- INITIALISATION MATÉRIELLE ---
            self.tx_gain = -20
            self.sdr.tx_hardwaregain_chan0 = int(self.tx_gain)
            self.sdr.rx_gain_control_mode_chan0 = 'slow_attack'
            self.rx_gain = 20
            
            self.sdr.rx_buffer_size = 1024
            self.sdr.tx_destroy_buffer()
        except Exception as e:
            print(f"Erreur PlutoSDR : {e}"); exit()

        # --- PARAMÈTRES DE NAVIGATION ---
        self.sig_freq, self.sig_type = 100_000, 'Sinus'
        self.active_plot = 0 # 0:Time, 1:Freq, 2:IQ
        self.paused = False
        
        # Peaks & Historique
        self.peak_f = None
        self.peak_t_pos, self.peak_t_neg = None, None
        self.peak_iq_accum = None
        
        # Zooms [Time, Freq, IQ]
        self.zx = [1.0, 1.0, 1.0] 
        self.zy = [1.5, 80.0, 1.5] 

        # --- INTERFACE 2x3 (Grille 2x4 pour centrage) ---
        self.fig = plt.figure(figsize=(15, 9), facecolor='#0b0b0b')
        grid = self.fig.add_gridspec(2, 4, hspace=0.35, wspace=0.4)
        
        self.ax_t = self.fig.add_subplot(grid[0, :2])
        self.ax_f = self.fig.add_subplot(grid[0, 2:])
        self.ax_i = self.fig.add_subplot(grid[1, 1:3])
        self.axs = [self.ax_t, self.ax_f, self.ax_i]
        
        # --- LIGNES ---
        # 1. Temps
        self.line_i, = self.ax_t.plot([], [], '#00d4ff', lw=0.8, zorder=3, label="RX (Réel)")
        self.line_q, = self.ax_t.plot([], [], '#00ff41', lw=0.8, alpha=0.5, zorder=3)
        self.line_th, = self.ax_t.plot([], [], 'r--', alpha=0.4, lw=1, zorder=2, label="TX (Théorie)")
        self.line_tp, = self.ax_t.plot([], [], '#ffaa00', lw=0.5, alpha=0.3, zorder=1)
        self.line_tn, = self.ax_t.plot([], [], '#ffaa00', lw=0.5, alpha=0.3, zorder=1)
        
        # 2. Spectre
        self.line_f, = self.ax_f.plot([], [], '#ff0055', lw=1, zorder=2)
        self.line_p, = self.ax_f.plot([], [], '#ffaa00', lw=0.8, alpha=0.3, zorder=1)
        
        # 3. Constellation
        self.line_iq, = self.ax_i.plot([], [], 'o', color='#00d4ff', ms=2, alpha=0.7, zorder=2)
        self.line_iqp, = self.ax_i.plot([], [], 'o', color='#ffaa00', ms=1, alpha=0.15, zorder=1)

        self.setup_ui()
        self.update_tx()
        
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.fig, self.update, interval=30, cache_frame_data=False)
        
        plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.08)
        plt.show()

    def setup_ui(self):
        self.ax_t.legend(loc='upper right', fontsize='xx-small', framealpha=0.2)
        self.ax_i.set_aspect('equal', adjustable='box')
        for ax in self.axs: ax.grid(True, color='#222222', linestyle=':')
        
        self.sidebar = self.fig.text(0.76, 0.25, "", color='#00d4ff', fontsize=9, 
                                    verticalalignment='center',
                                    bbox=dict(boxstyle='round', facecolor='#161616', alpha=0.8))

    def update_tx(self):
        self.sdr.tx_destroy_buffer()
        t = np.arange(4096) / self.fs
        phi = 2 * np.pi * self.sig_freq * t
        if self.sig_type == 'Sinus': iq = np.exp(1j*phi)
        elif self.sig_type == 'Carré': iq = np.sign(np.cos(phi)) + 1j*np.sign(np.sin(phi))
        else: iq = (2*np.abs(2*(t*self.sig_freq-np.floor(t*self.sig_freq+0.5)))-1) + \
                   1j*(2*np.abs(2*(t*self.sig_freq-np.floor(t*self.sig_freq+0.25)))-1)
        self.sdr.tx_cyclic_buffer = True
        self.sdr.tx(iq * (2**13))

    def update(self, frame):
        if self.paused: return
        rx = self.sdr.rx() / (2**11)
        t_ms = np.arange(len(rx)) / self.fs * 1000
        
        titles = ["1. TEMPOREL", "2. SPECTRE", "3. CONSTELLATION"]
        for i, ax in enumerate(self.axs):
            ax.set_title(titles[i], color='#00d4ff' if i == self.active_plot else 'white', 
                        weight='bold', fontsize=12 if i == self.active_plot else 10)

        # 1. TEMPOREL + Triple Peak + Théorie
        if self.peak_t_pos is None: self.peak_t_pos, self.peak_t_neg = rx.real.copy(), rx.real.copy()
        else: self.peak_t_pos, self.peak_t_neg = np.maximum(self.peak_t_pos, rx.real), np.minimum(self.peak_t_neg, rx.real)
        
        self.line_i.set_data(t_ms, rx.real)
        self.line_q.set_data(t_ms, rx.imag)
        self.line_th.set_data(t_ms, np.cos(2*np.pi*self.sig_freq*(t_ms/1000)))
        self.line_tp.set_data(t_ms, self.peak_t_pos)
        self.line_tn.set_data(t_ms, self.peak_t_neg)
        self.ax_t.set_xlim(0, t_ms[-1] / self.zx[0]); self.ax_t.set_ylim(-self.zy[0], self.zy[0])

        # 2. SPECTRE + Peak
        f_khz = np.fft.fftshift(np.fft.fftfreq(len(rx), 1/self.fs)) / 1000
        psd = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx))/len(rx)+1e-6))
        if self.peak_f is None or len(self.peak_f) != len(psd): self.peak_f = psd
        else: self.peak_f = np.maximum(self.peak_f, psd)
        
        self.line_f.set_data(f_khz, psd); self.line_p.set_data(f_khz, self.peak_f)
        span = (self.fs/2000) / self.zx[1]; self.ax_f.set_xlim(-span, span); self.ax_f.set_ylim(-self.zy[1], 10)

        # 3. IQ + Persistance
        if self.peak_iq_accum is None: self.peak_iq_accum = rx.copy()
        else: self.peak_iq_accum = np.concatenate([self.peak_iq_accum[-20000:], rx])
        
        self.line_iq.set_data(rx.real, rx.imag); self.line_iqp.set_data(self.peak_iq_accum.real, self.peak_iq_accum.imag)
        self.ax_i.set_xlim(-self.zy[2], self.zy[2]); self.ax_i.set_ylim(-self.zy[2], self.zy[2])

        # INFO SIDEBAR
        mode_rx = self.sdr.rx_gain_control_mode_chan0
        rx_val = "AUTO" if mode_rx != 'manual' else f"{self.rx_gain}dB"
        self.sidebar.set_text(f"--- LOOPBACK PRO ---\n"
                              f"FOCUS: {titles[self.active_plot].split('.')[1]}\n\n"
                              f"[T] ou [1,2,3] : Focus\n"
                              f"[+/-] : Zoom X\n"
                              f"[UP/DN]: Zoom Y\n\n"
                              f"[L/R] : Freq TX\n"
                              f"[W] : Forme Onde\n"
                              f"[PgUp/Dn]: RX Gain\n"
                              f"[Home/End]: TX Gain\n"
                              f"[A] : AGC | [R] : Reset\n"
                              f"[Q] : Quitter\n\n"
                              f"F: {self.sig_freq/1000:.1f} kHz\n"
                              f"RX: {rx_val} | TX: {self.tx_gain}dB")

    def on_key(self, event):
        # SÉLECTION
        if event.key == 't': self.active_plot = (self.active_plot + 1) % 3
        elif event.key in ['1','2','3']: self.active_plot = int(event.key)-1
        
        # ZOOM
        elif event.key == 'up': self.zy[self.active_plot] *= 0.8
        elif event.key == 'down': self.zy[self.active_plot] *= 1.2
        elif event.key == '+': self.zx[self.active_plot] *= 1.4
        elif event.key == '-': self.zx[self.active_plot] = max(1.0, self.zx[self.active_plot] / 1.4)
        
        # SIGNAL & NAVIGATION
        elif event.key == 'right': self.sig_freq += 10000; self.update_tx()
        elif event.key == 'left': self.sig_freq = max(0, self.sig_freq - 10000); self.update_tx()
        elif event.key == 'w':
            self.sig_type = ['Sinus', 'Carré', 'Triangle'][(['Sinus', 'Carré', 'Triangle'].index(self.sig_type)+1)%3]
            self.update_tx()
            
        # GAINS
        elif event.key == 'pageup': 
            self.sdr.rx_gain_control_mode_chan0 = 'manual'
            self.rx_gain = min(73, self.rx_gain + 2); self.sdr.rx_hardwaregain_chan0 = int(self.rx_gain)
        elif event.key == 'pagedown': 
            self.sdr.rx_gain_control_mode_chan0 = 'manual'
            self.rx_gain = max(0, self.rx_gain - 2); self.sdr.rx_hardwaregain_chan0 = int(self.rx_gain)
        elif event.key == 'home': 
            self.tx_gain = min(0, self.tx_gain + 2); self.sdr.tx_hardwaregain_chan0 = int(self.tx_gain)
        elif event.key == 'end': 
            self.tx_gain = max(-89, self.tx_gain - 2); self.sdr.tx_hardwaregain_chan0 = int(self.tx_gain)
        elif event.key == 'a': self.sdr.rx_gain_control_mode_chan0 = 'slow_attack'
        
        # UTILS
        elif event.key == 'r': self.peak_f = self.peak_t_pos = self.peak_t_neg = self.peak_iq_accum = None
        elif event.key == ' ': self.paused = not self.paused
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    PlutoLoopbackFinalPro()