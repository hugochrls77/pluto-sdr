import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator
from gui_manager import LabGUI

class PlutoSignalStudio:
    def __init__(self):
        self.fs = 5_000_000
        self.hw = PlutoDevice(fs=self.fs)
        self.ui = LabGUI(["1. TEMPOREL", "2. SPECTRE", "3. CONSTELLATION"])
        
        self.sig_list = ['Sinus', 'Carré', 'Triangle', 'Scie', 'Bruit', 'QPSK_Raw', 'QPSK_Filtered']
        self.sig_type, self.sig_freq = 'Sinus', 110_000
        self.active_plot, self.paused = 0, False
        self.zx, self.zy = [1.0, 1.0, 1.0], [0.8, 130.0, 0.6]
        self.peak_f = self.peak_t_pos = self.peak_t_neg = self.peak_iq_accum = None
        self.peak_enabled = False  # Activé par défaut

        # Initialisation des lignes
        self.line_i, = self.ui.ax_t.plot([], [], '#00d4ff', lw=0.8, zorder=3)
        self.line_q, = self.ui.ax_t.plot([], [], '#00ff41', lw=0.8, alpha=0.5, zorder=3)
        self.line_tp, = self.ui.ax_t.plot([], [], '#ffaa00', lw=0.5, alpha=0.3, zorder=1)
        self.line_tn, = self.ui.ax_t.plot([], [], '#ffaa00', lw=0.5, alpha=0.3, zorder=1)
        self.line_f, = self.ui.ax_f.plot([], [], '#ff0055', lw=1, zorder=2)
        self.line_p, = self.ui.ax_f.plot([], [], '#ffaa00', lw=0.8, alpha=0.3, zorder=1)
        self.line_iq, = self.ui.ax_i.plot([], [], 'o', color='#00d4ff', ms=2, alpha=0.7)
        self.line_iqp, = self.ui.ax_i.plot([], [], 'o', color='#ffaa00', ms=1, alpha=0.15)

        self.update_tx()
        self.ui.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.ui.fig, self.update, interval=30, cache_frame_data=False)
        plt.show()

    def update_tx(self):
        iq = SignalGenerator.generate(self.sig_type, self.sig_freq, self.fs)
        self.hw.tx(iq)

    def update(self, frame):
        if self.paused: return
        
        # 1. ACQUISITION ET CALCULS DE BASE
        rx = self.hw.rx()
        t_ms = np.arange(len(rx)) / self.fs * 1000
        
        # Calcul du Spectre (FFT) - On le fait ICI pour éviter l'UnboundLocalError
        f_khz = np.fft.fftshift(np.fft.fftfreq(len(rx), 1/self.fs)) / 1000
        psd = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx))/len(rx)+1e-6))
        
        self.ui.update_focus(self.active_plot)

        # 2. LOGIQUE DES PEAKS (Conditionnelle)
        if self.peak_enabled:
            # Peaks Temporels
            if self.peak_t_pos is None: 
                self.peak_t_pos, self.peak_t_neg = rx.real.copy(), rx.real.copy()
            else: 
                self.peak_t_pos, self.peak_t_neg = np.maximum(self.peak_t_pos, rx.real), np.minimum(self.peak_t_neg, rx.real)
            
            # Peak Spectre
            if self.peak_f is None or len(self.peak_f) != len(psd): 
                self.peak_f = psd
            else: 
                self.peak_f = np.maximum(self.peak_f, psd)
            
            # Persistance IQ
            if self.peak_iq_accum is None: 
                self.peak_iq_accum = rx.copy()
            else: 
                self.peak_iq_accum = np.concatenate([self.peak_iq_accum[-20000:], rx])

            # Mise à jour des lignes de Peaks
            self.line_tp.set_data(t_ms, self.peak_t_pos)
            self.line_tn.set_data(t_ms, self.peak_t_neg)
            self.line_p.set_data(f_khz, self.peak_f)
            self.line_iqp.set_data(self.peak_iq_accum.real, self.peak_iq_accum.imag)
        else:
            # Si désactivé, on vide les lignes
            self.line_tp.set_data([], [])
            self.line_tn.set_data([], [])
            self.line_p.set_data([], [])
            self.line_iqp.set_data([], [])

        # 3. MISE À JOUR DES TRACÉS "LIVE"
        # Temporel
        self.line_i.set_data(t_ms, rx.real)
        self.line_q.set_data(t_ms, rx.imag)
        self.ui.ax_t.set_xlim(0, t_ms[-1] / self.zx[0])
        self.ui.ax_t.set_ylim(-self.zy[0], self.zy[0])

        # Spectre
        self.line_f.set_data(f_khz, psd)
        span = (self.fs/2000) / self.zx[1]
        self.ui.ax_f.set_xlim(-span, span)
        self.ui.ax_f.set_ylim(-self.zy[1], 10)

        # IQ (Direct)
        self.line_iq.set_data(rx.real, rx.imag)
        self.ui.ax_i.set_xlim(-self.zy[2], self.zy[2])
        self.ui.ax_i.set_ylim(-self.zy[2], self.zy[2])

        # 4. SIDEBAR
        mode = self.hw.sdr.rx_gain_control_mode_chan0
        rx_status = "AUTO" if mode != 'manual' else f"{self.hw.rx_gain}dB"
        tx_status = "AUTO" if mode != 'manual' else f"{self.hw.tx_gain}dB"
        peak_status = "ON" if self.peak_enabled else "OFF" # Définition de la variable manquante
        
        self.ui.sidebar.set_text(
            f"--- PLUTO SIGNAL STUDIO ---\n"
            f"SIG: {self.sig_type} | F: {self.sig_freq/1000:.1f}kHz\n\n"
            f" [VUE]\n"
            f" [T] ou [1,2,3] : Focus\n"
            f" [+/-] : Zoom X | [↑/↓] : Zoom Y\n\n"
            f" [SIGNAL]\n"
            f" [←/→] : Freq Sig | [W] : Type\n\n"
            f" [GAINS]\n"
            f" [PgUp/Dn]  : RX Gain ({rx_status})\n"
            f" [Home/End] : TX Gain ({tx_status})\n"
            f" [A] : Mode AUTO | [R] : Reset Peaks\n\n"
            f" [P] : Peak Hold ({peak_status})\n\n"
            f" [SYSTEME]\n"
            f" [SPACE] : Pause | [Q] : Quitter"
        )

    def on_key(self, event):
        if event.key in ['1','2','3']: self.active_plot = int(event.key)-1
        elif event.key == 't': self.active_plot = (self.active_plot + 1) % 3
        elif event.key == 'up': self.zy[self.active_plot] *= 0.8
        elif event.key == 'down': self.zy[self.active_plot] *= 1.2
        elif event.key == '+': self.zx[self.active_plot] *= 1.4
        elif event.key == '-': self.zx[self.active_plot] = max(1.0, self.zx[self.active_plot] / 1.4)
        elif event.key == 'right': self.sig_freq += 10000; self.update_tx()
        elif event.key == 'left': self.sig_freq = max(0, self.sig_freq - 10000); self.update_tx()
        elif event.key == 'w':
            self.sig_type = self.sig_list[(self.sig_list.index(self.sig_type) + 1) % len(self.sig_list)]
            self.update_tx(); self.peak_f = None
        elif event.key == 'pageup': self.hw.set_rx_gain('manual', min(73, self.hw.rx_gain+2))
        elif event.key == 'pagedown': self.hw.set_rx_gain('manual', max(0, self.hw.rx_gain-2))
        elif event.key == 'home': self.hw.set_tx_gain('manual', min(0, self.hw.tx_gain+2))
        elif event.key == 'end': self.hw.set_tx_gain('manual', max(-89, self.hw.tx_gain-2))
        elif event.key == 'a': 
            self.hw.set_rx_gain('slow_attack')
            self.hw.set_tx_gain('slow_attack')
        elif event.key == 'r': self.peak_f = self.peak_t_pos = self.peak_t_neg = self.peak_iq_accum = None
        elif event.key == 'q': plt.close()
        elif event.key == 'p':
            self.peak_enabled = not self.peak_enabled
            if not self.peak_enabled:
                # Optionnel : On réinitialise les données quand on désactive
                self.peak_f = self.peak_t_pos = self.peak_t_neg = self.peak_iq_accum = None

if __name__ == "__main__":
    PlutoSignalStudio()