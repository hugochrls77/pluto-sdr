import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Style Dark Lab Pro
plt.style.use('dark_background')
plt.rcParams['font.family'] = 'monospace'
plt.rcParams['keymap.save'] = '' 

class SDRSimAnalyzerPro:
    def __init__(self):
        # --- PARAMÈTRES DU SIGNAL ---
        self.fs = 2000
        self.n_points = 1024
        self.sig_freq = 100
        self.sig_type = 'Sinus'
        
        # --- ÉTAT DU SYSTÈME ---
        self.active_plot = 1 # 0:Time, 1:Freq, 2:IQ
        self.paused = False
        self.peak_f = None
        self.peak_t_pos, self.peak_t_neg = None, None
        self.peak_iq_accum = None
        
        # Zooms [Time, Freq, IQ]
        self.zx = [1.0, 1.0, 1.0] 
        self.zy = [1.5, 60.0, 1.5] 

        # --- INTERFACE 2x3 ---
        self.fig = plt.figure(figsize=(15, 9), facecolor='#0b0b0b')
        grid = self.fig.add_gridspec(2, 4, hspace=0.35, wspace=0.4)
        
        self.ax_t = self.fig.add_subplot(grid[0, :2])
        self.ax_f = self.fig.add_subplot(grid[0, 2:])
        self.ax_i = self.fig.add_subplot(grid[1, 1:3])
        self.axs = [self.ax_t, self.ax_f, self.ax_i]
        
        # --- LIGNES ---
        # Temps
        self.line_i, = self.ax_t.plot([], [], '#00d4ff', lw=0.8, zorder=3, label="Réel (Bruité)")
        self.line_th, = self.ax_t.plot([], [], 'r--', alpha=0.4, lw=1, zorder=2, label="Théorie")
        self.line_tp, = self.ax_t.plot([], [], '#ffaa00', lw=0.5, alpha=0.2, zorder=1)
        self.line_tn, = self.ax_t.plot([], [], '#ffaa00', lw=0.5, alpha=0.2, zorder=1)
        
        # Spectre
        self.line_f, = self.ax_f.plot([], [], '#ff0055', lw=1, zorder=2)
        self.line_p, = self.ax_f.plot([], [], '#ffaa00', lw=0.8, alpha=0.3, zorder=1)
        
        # IQ
        self.line_iq, = self.ax_i.plot([], [], 'o', color='#00d4ff', ms=2, alpha=0.7, zorder=2)
        self.line_iqp, = self.ax_i.plot([], [], 'o', color='#ffaa00', ms=1, alpha=0.1, zorder=1)

        self.setup_ui()
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

    def generate_sim_data(self):
        t = np.arange(self.n_points) / self.fs
        phi = 2 * np.pi * self.sig_freq * t
        if self.sig_type == 'Sinus': iq = np.exp(1j * phi)
        elif self.sig_type == 'Carré': iq = np.sign(np.cos(phi)) + 1j * np.sign(np.sin(phi))
        else: # Triangle
            i = 2 * np.abs(2 * (t * self.sig_freq - np.floor(t * self.sig_freq + 0.5))) - 1
            q = 2 * np.abs(2 * (t * self.sig_freq - np.floor(t * self.sig_freq + 0.25))) - 1
            iq = i + 1j * q
        # Bruit blanc gaussien complexe
        noise = (np.random.normal(0, 0.08, self.n_points) + 1j*np.random.normal(0, 0.08, self.n_points))
        return t, iq, iq + noise

    def update(self, frame):
        if self.paused: return
        t, theory, real = self.generate_sim_data()
        
        # Titres Focus
        titles = ["1. TEMPOREL (Simulation)", "2. SPECTRE (FFT)", "3. CONSTELLATION"]
        for i, ax in enumerate(self.axs):
            ax.set_title(titles[i], color='#00d4ff' if i == self.active_plot else 'white', 
                        weight='bold', fontsize=12 if i == self.active_plot else 10)

        # 1. TEMPOREL + Peak + Théorie
        if self.peak_t_pos is None: self.peak_t_pos, self.peak_t_neg = real.real.copy(), real.real.copy()
        else: self.peak_t_pos, self.peak_t_neg = np.maximum(self.peak_t_pos, real.real), np.minimum(self.peak_t_neg, real.real)
        
        self.line_i.set_data(t, real.real)
        self.line_th.set_data(t, theory.real)
        self.line_tp.set_data(t, self.peak_t_pos)
        self.line_tn.set_data(t, self.peak_t_neg)
        self.ax_t.set_xlim(0, t[-1] / self.zx[0]); self.ax_t.set_ylim(-self.zy[0], self.zy[0])

        # 2. SPECTRE + Peak
        f = np.fft.fftfreq(self.n_points, 1/self.fs)
        def get_db(s): return 20 * np.log10(np.abs(np.fft.fft(s)) / self.n_points + 1e-6)
        psd = get_db(real)
        if self.peak_f is None: self.peak_f = psd
        else: self.peak_f = np.maximum(self.peak_f, psd)
        
        idx = np.argsort(f)
        self.line_f.set_data(f[idx], psd[idx]); self.line_p.set_data(f[idx], self.peak_f[idx])
        span = (self.fs/2) / self.zx[1]
        self.ax_f.set_xlim(-span, span); self.ax_f.set_ylim(-self.zy[1], 10)

        # 3. IQ + Persistance
        if self.peak_iq_accum is None: self.peak_iq_accum = real.copy()
        else: self.peak_iq_accum = np.concatenate([self.peak_iq_accum[-20000:], real])
        
        self.line_iq.set_data(real.real, real.imag)
        self.line_iqp.set_data(self.peak_iq_accum.real, self.peak_iq_accum.imag)
        self.ax_i.set_xlim(-self.zy[2], self.zy[2]); self.ax_i.set_ylim(-self.zy[2], self.zy[2])

        # SIDEBAR
        self.sidebar.set_text(f"--- SIMULATEUR PRO ---\n"
                              f"[T] ou [1,2,3] : Focus\n"
                              f"[+/-] : Zoom X\n"
                              f"[UP/DN]: Zoom Y\n\n"
                              f"[L/R] : Fréquence\n"
                              f"[W] : Forme Onde\n"
                              f"[R] : Reset Peaks\n"
                              f"[SPACE] : Pause\n"
                              f"[Q] : Quitter\n"
                              f"--------------------\n"
                              f"FREQ : {self.sig_freq} Hz\n"
                              f"TYPE : {self.sig_type}")

    def on_key(self, event):
        if event.key == 't': self.active_plot = (self.active_plot + 1) % 3
        elif event.key in ['1','2','3']: self.active_plot = int(event.key)-1
        elif event.key == 'up': self.zy[self.active_plot] *= 0.8
        elif event.key == 'down': self.zy[self.active_plot] *= 1.2
        elif event.key == '+': self.zx[self.active_plot] *= 1.4
        elif event.key == '-': self.zx[self.active_plot] = max(1.0, self.zx[self.active_plot] / 1.4)
        elif event.key == 'right': self.sig_freq = min(1000, self.sig_freq + 10)
        elif event.key == 'left': self.sig_freq = max(0, self.sig_freq - 10)
        elif event.key == 'w':
            types = ['Sinus', 'Carré', 'Triangle']
            self.sig_type = types[(types.index(self.sig_type) + 1) % 3]
        elif event.key == 'r': self.peak_f = self.peak_t_pos = self.peak_t_neg = self.peak_iq_accum = None
        elif event.key == ' ': self.paused = not self.paused
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    SDRSimAnalyzerPro()