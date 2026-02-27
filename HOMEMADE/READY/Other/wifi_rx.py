import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import adi

# Style Dark Lab
plt.style.use('dark_background')
plt.rcParams['font.family'] = 'monospace'
plt.rcParams['keymap.save'] = '' 

class PlutoUltraScannerFinalUI:
    def __init__(self, ip="ip:192.168.2.1"):
        try:
            self.sdr = adi.Pluto(ip)
            self.fs = 2_000_000 
            self.sdr.sample_rate = self.fs
            self.center_freq = 2_412_000_000 
            self.sdr.rx_lo = int(self.center_freq)
            self.sdr.tx_lo = int(self.center_freq)
            
            self.sdr.rx_gain_control_mode_chan0 = 'slow_attack'
            self.rx_gain = 30
            self.tx_gain = -20
            self.sdr.tx_hardwaregain_chan0 = int(self.tx_gain)
            
            self.sdr.rx_buffer_size = 4096*8
            self.sdr.tx_destroy_buffer()
        except: print("PlutoSDR non détecté."); exit()

        # --- PARAMÈTRES DE NAVIGATION ---
        self.active_plot = 1 
        self.peak_hold = None
        self.peak_t_pos, self.peak_t_neg = None, None
        self.peak_iq_accum = None
        self.paused = False
        
        self.zx = [1.0, 1.0, 1.0] 
        self.zy = [1.2, 90.0, 1.2] 

        # --- NOUVELLE GRILLE 2x3 ---
        self.fig = plt.figure(figsize=(15, 9), facecolor='#0b0b0b')
        # On définit une grille de 2 lignes et 4 colonnes pour un centrage plus fin
        grid = self.fig.add_gridspec(2, 4, hspace=0.35, wspace=0.4)
        
        # Haut : 2 graphes qui prennent chacun 2 colonnes (50% de largeur chacun)
        self.ax_t = self.fig.add_subplot(grid[0, :2])
        self.ax_f = self.fig.add_subplot(grid[0, 2:])
        
        # Bas : Constellation au centre (colonnes 1 et 2 sur 0,1,2,3)
        self.ax_i = self.fig.add_subplot(grid[1, 1:3])
        self.axs = [self.ax_t, self.ax_f, self.ax_i]
        
        # Lignes
        self.line_i, = self.ax_t.plot([], [], '#00d4ff', lw=0.8, zorder=2)
        self.line_q, = self.ax_t.plot([], [], '#00ff41', lw=0.8, alpha=0.5, zorder=2)
        self.line_tp, = self.ax_t.plot([], [], '#ffaa00', lw=0.5, alpha=0.3, zorder=1)
        self.line_tn, = self.ax_t.plot([], [], '#ffaa00', lw=0.5, alpha=0.3, zorder=1)
        
        self.line_f, = self.ax_f.plot([], [], '#ff0055', lw=1, zorder=2)
        self.line_p, = self.ax_f.plot([], [], '#ffaa00', lw=0.8, alpha=0.3, zorder=1)
        
        self.line_iq, = self.ax_i.plot([], [], 'o', color='#00d4ff', ms=2, alpha=0.6, zorder=2)
        self.line_iqp, = self.ax_i.plot([], [], 'o', color='#ffaa00', ms=1, alpha=0.15, zorder=1)

        self.setup_ui()
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.fig, self.update, interval=30, cache_frame_data=False)
        
        # On utilise toute la largeur disponible
        plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.08)
        plt.show()

    def setup_ui(self):
        for ax in self.axs: ax.grid(True, color='#222222', linestyle=':')
        self.ax_i.set_aspect('equal', adjustable='box') # Repère orthonormé
        
        # Sidebar déplacée en bas à droite (coordonnées relatives à la figure)
        self.sidebar = self.fig.text(0.76, 0.25, "", color='#00d4ff', fontsize=9, 
                                    verticalalignment='center',
                                    bbox=dict(boxstyle='round', facecolor='#161616', alpha=0.8))

    def update(self, frame):
        if self.paused: return
        rx = self.sdr.rx() / (2**11)
        
        titles = ["1. TEMPOREL", "2. SPECTRE WiFi", "3. CONSTELLATION"]
        for i, ax in enumerate(self.axs):
            ax.set_title(titles[i], color='#00d4ff' if i == self.active_plot else 'white', 
                        weight='bold', fontsize=12 if i == self.active_plot else 10)

        # 1. TEMPOREL
        t = np.arange(len(rx)) / self.fs * 1e6
        if self.peak_t_pos is None: self.peak_t_pos, self.peak_t_neg = rx.real.copy(), rx.real.copy()
        else: self.peak_t_pos, self.peak_t_neg = np.maximum(self.peak_t_pos, rx.real), np.minimum(self.peak_t_neg, rx.real)
        self.line_i.set_data(t, rx.real); self.line_q.set_data(t, rx.imag)
        self.line_tp.set_data(t, self.peak_t_pos); self.line_tn.set_data(t, self.peak_t_neg)
        self.ax_t.set_xlim(0, t[-1] / self.zx[0]); self.ax_t.set_ylim(-self.zy[0], self.zy[0])

        # 2. SPECTRE
        f_raw = np.fft.fftshift(np.fft.fftfreq(len(rx), 1/self.fs))
        psd = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx))/len(rx)+1e-6))
        if self.peak_hold is None or len(self.peak_hold) != len(psd): self.peak_hold = psd
        else: self.peak_hold = np.maximum(self.peak_hold, psd)
        f_axis = (f_raw + self.center_freq) / 1e6
        self.line_f.set_data(f_axis, psd); self.line_p.set_data(f_axis, self.peak_hold)
        span = (self.fs / 2e6) / self.zx[1]
        self.ax_f.set_xlim((self.center_freq/1e6) - span, (self.center_freq/1e6) + span); self.ax_f.set_ylim(-self.zy[1], 5)

        # 3. IQ
        if self.peak_iq_accum is None: self.peak_iq_accum = rx.copy()
        else: self.peak_iq_accum = np.concatenate([self.peak_iq_accum[-50000:], rx]) # Persistance équilibrée
        self.line_iq.set_data(rx.real, rx.imag); self.line_iqp.set_data(self.peak_iq_accum.real, self.peak_iq_accum.imag)
        self.ax_i.set_xlim(-self.zy[2], self.zy[2]); self.ax_i.set_ylim(-self.zy[2], self.zy[2])

        # INFOS SIDEBAR
        mode_gain = self.sdr.rx_gain_control_mode_chan0
        rx_status = "AUTO" if mode_gain != 'manual' else f"{self.rx_gain}dB"
        self.sidebar.set_text(f"--- COMMANDES ---\n"
                              f"[T] ou [1,2,3] : Focus\n"
                              f"[+/-] : Zoom X\n"
                              f"[UP/DN]: Zoom Y\n"
                              f"[L/R] : Scan Freq\n"
                              f"[PgUp/Dn]: RX Gain\n"
                              f"[Home/End]: TX Gain\n"
                              f"[A] : AGC | [R] : Reset\n"
                              f"[Q] : Quitter\n\n"
                              f"F: {self.center_freq/1e6:.1f} MHz\n"
                              f"RX: {rx_status} | TX: {self.tx_gain}dB")

    def on_key(self, event):
        if event.key == 't': self.active_plot = (self.active_plot + 1) % 3
        elif event.key in ['1','2','3']: self.active_plot = int(event.key)-1
        elif event.key == 'up': self.zy[self.active_plot] *= 0.8
        elif event.key == 'down': self.zy[self.active_plot] *= 1.2
        elif event.key == '+': self.zx[self.active_plot] *= 1.4
        elif event.key == '-': self.zx[self.active_plot] = max(1.0, self.zx[self.active_plot] / 1.4)
        elif event.key == 'right': self.center_freq += 5e6; self.sdr.rx_lo = int(self.center_freq); self.sdr.tx_lo = int(self.center_freq); self.peak_hold = None
        elif event.key == 'left': self.center_freq -= 5e6; self.sdr.rx_lo = int(self.center_freq); self.sdr.tx_lo = int(self.center_freq); self.peak_hold = None
        elif event.key == 'pageup': self.sdr.rx_gain_control_mode_chan0 = 'manual'; self.rx_gain = min(73, self.rx_gain + 2); self.sdr.rx_hardwaregain_chan0 = int(self.rx_gain)
        elif event.key == 'pagedown': self.sdr.rx_gain_control_mode_chan0 = 'manual'; self.rx_gain = max(0, self.rx_gain - 2); self.sdr.rx_hardwaregain_chan0 = int(self.rx_gain)
        elif event.key == 'home': self.tx_gain = min(0, self.tx_gain + 2); self.sdr.tx_hardwaregain_chan0 = int(self.tx_gain)
        elif event.key == 'end': self.tx_gain = max(-89, self.tx_gain - 2); self.sdr.tx_hardwaregain_chan0 = int(self.tx_gain)
        elif event.key == 'a': self.sdr.rx_gain_control_mode_chan0 = 'slow_attack'
        elif event.key == 'r': self.peak_hold = self.peak_t_pos = self.peak_t_neg = self.peak_iq_accum = None
        elif event.key == ' ': self.paused = not self.paused
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    PlutoUltraScannerFinalUI()