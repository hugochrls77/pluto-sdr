import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sdr_device import PlutoDevice
from signal_generator import SignalGenerator
from gui_manager import LabGUI

class PlutoSignalComparator:
    def __init__(self):
        self.fs = 2_000_000
        self.hw = PlutoDevice(fs=self.fs)
        self.ui = LabGUI(["1. COMPARAISON TEMPORELLE", "2. SPECTRE TX/RX", "3. COMPARAISON IQ"])
        
        # Configuration initiale (selon tes screenshots)
        self.sig_list = ['Sinus', 'Carré', 'Triangle', 'Scie', 'Bruit', 'QPSK_Raw', 'QPSK_Filtered']
        self.sig_type, self.sig_freq = 'Sinus', 110_000
        self.active_plot, self.paused = 0, False
        self.zx, self.zy = [4.0, 1.0, 1.0], [0.8, 130.0, 0.6]
        
        self.tx_data = None # Stockage du signal numérique réel envoyé

        # --- INITIALISATION DES LIGNES (TX vs RX) ---
        # 1. TEMPOREL : RX (Cyan) vs TX (Rouge pointillé)
        self.line_rx, = self.ui.ax_t.plot([], [], '#00d4ff', lw=0.8, zorder=3, label="RX (Reçu)")
        self.line_tx, = self.ui.ax_t.plot([], [], 'red', lw=1, alpha=0.5, ls='--', zorder=2, label="TX (Envoyé)")

        # 2. SPECTRE : RX (Rose) vs TX (Blanc transparent)
        self.line_f_rx, = self.ui.ax_f.plot([], [], '#ff0055', lw=1, zorder=3, label="RX")
        self.line_f_tx, = self.ui.ax_f.plot([], [], 'white', lw=0.8, alpha=0.3, zorder=2, label="TX")

        # 3. CONSTELLATION : RX (Points Cyan) vs TX (Croix Rouges)
        self.line_iq_rx, = self.ui.ax_i.plot([], [], 'o', color='#00d4ff', ms=2, alpha=0.7, zorder=3)
        self.line_iq_tx, = self.ui.ax_i.plot([], [], 'x', color='red', ms=4, alpha=0.4, zorder=2)

        self.ui.ax_t.legend(loc='upper right', fontsize='xx-small', framealpha=0.2)
        self.update_tx()
        
        self.ui.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.ui.fig, self.update, interval=30, cache_frame_data=False)
        plt.show()

    def update_tx(self):
        # On génère le signal et on le garde en mémoire pour comparer
        self.tx_data = SignalGenerator.generate(self.sig_type, self.sig_freq, self.fs)
        self.hw.tx(self.tx_data)

    def update(self, frame):
        if self.paused: return
        
        # 1. ACQUISITION
        rx = self.hw.rx()
        tx = self.tx_data[:len(rx)] # Synchronisation de la taille du buffer
        t_ms = np.arange(len(rx)) / self.fs * 1000
        
        # 2. CALCULS SPECTRE
        f_khz = np.fft.fftshift(np.fft.fftfreq(len(rx), 1/self.fs)) / 1000
        psd_rx = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(rx))/len(rx)+1e-6))
        psd_tx = np.fft.fftshift(20*np.log10(np.abs(np.fft.fft(tx))/len(tx)+1e-6))
        
        snr_val = np.max(psd_rx) - np.median(psd_rx)
        rx_c = rx.real - np.mean(rx.real)
        tx_c = tx.real - np.mean(tx.real)
        corr = np.correlate(rx_c, tx_c, mode='full')
        delay_samples = np.argmax(corr) - (len(tx_c) - 1)
        latency_us = (delay_samples / self.fs) * 1e6

        self.ui.update_focus(self.active_plot)

        # 3. MISE À JOUR DES TRACÉS
        # Temporel
        self.line_rx.set_data(t_ms, rx.real)
        self.line_tx.set_data(t_ms, tx.real)
        self.ui.ax_t.set_xlim(0, t_ms[-1] / self.zx[0])
        self.ui.ax_t.set_ylim(-self.zy[0], self.zy[0])

        # Spectre
        self.line_f_rx.set_data(f_khz, psd_rx)
        self.line_f_tx.set_data(f_khz, psd_tx)
        span = (self.fs/2000) / self.zx[1]
        self.ui.ax_f.set_xlim(-span, span); self.ui.ax_f.set_ylim(-self.zy[1], 10)

        # IQ (Superposition directe)
        self.line_iq_rx.set_data(rx.real, rx.imag)
        self.line_iq_tx.set_data(tx.real, tx.imag)
        self.ui.ax_i.set_xlim(-self.zy[2], self.zy[2]); self.ui.ax_i.set_ylim(-self.zy[2], self.zy[2])

        # 4. SIDEBAR
        mode = self.hw.sdr.rx_gain_control_mode_chan0
        rx_stat = "AUTO" if mode != 'manual' else f"{self.hw.rx_gain}dB"
        tx_stat = f"{self.hw.tx_gain}dB"
        
        self.ui.sidebar.set_text(
            f"--- COMPARATEUR RX/TX ---\n"
            f"SIG: {self.sig_type} | F: {self.sig_freq/1000:.1f}kHz\n\n"
            f" [MESURES TEMPS RÉEL]\n"
            f" SNR RX  : {snr_val:.1f} dB\n"
            f" LATENCE : {latency_us:.2f} µs\n\n"
            f" [VUE]\n"
            f" [T] ou [1,2,3] : Focus\n"
            f" [+/-] : Zoom X | [↑/↓] : Zoom Y\n\n"
            f" [SIGNAL]\n"
            f" [←/→] : Freq Sig | [W] : Type\n\n"
            f" [GAINS]\n"
            f" [PgUp/Dn]  : RX Gain ({rx_stat})\n"
            f" [Home/End] : TX Gain ({tx_stat})\n"
            f" [A] : Mode AUTO\n\n"
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
            self.update_tx()
        elif event.key == 'pageup': self.hw.set_rx_gain('manual', min(73, self.hw.rx_gain+2))
        elif event.key == 'pagedown': self.hw.set_rx_gain('manual', max(0, self.hw.rx_gain-2))
        elif event.key == 'home': self.hw.set_tx_gain(min(0, self.hw.tx_gain+2))
        elif event.key == 'end': self.hw.set_tx_gain(max(-89, self.hw.tx_gain-2))
        elif event.key == 'a': 
            self.hw.set_rx_gain('slow_attack')
            self.hw.set_tx_gain(-20) 
        elif event.key == ' ': self.paused = not self.paused
        elif event.key == 'q': plt.close()

if __name__ == "__main__":
    PlutoSignalComparator()