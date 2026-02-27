# HOMEMADE/DRAFT/PlutoSFCW/turbo_motion_trigger.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys, os

sys.path.append(os.path.abspath("../../READY/PlutoDoppler"))
from sdr_device import PlutoDevice

class TurboMotionTrigger:
    def __init__(self):
        # 1. OPTIMISATION : On réduit à 10 points pour aller très vite
        self.f_start, self.f_step, self.n_steps = 2_100_000_000, 20_000_000, 10
        
        self.hw = PlutoDevice(fs=2_000_000, lo=self.f_start)
        self.hw.set_tx_gain('manual', -55)
        self.hw.set_rx_gain('manual', 35)
        
        self.prev_scan = None
        self.history = np.zeros(100)
        
        # Interface "Alarme"
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.line, = self.ax.plot(range(100), self.history, color='#00ff41', lw=2)
        
        self.ax.set_ylim(0, 1.0)
        self.ax.set_title("DÉTECTEUR DE PHASE ULTRA-SENSIBLE", color='cyan', fontsize=12)
        self.ax.set_ylabel("Intensité du changement (Phase)", fontsize=10)
        self.ax.grid(True, alpha=0.1)

        self.hw.tx(np.ones(1024, dtype=complex) * 0.3)
        # On accélère l'intervalle pour la réactivité
        self.ani = FuncAnimation(self.fig, self.update, interval=30, blit=True)
        plt.show()

    def get_fast_scan(self):
        complex_data = []
        for i in range(self.n_steps):
            self.hw.set_lo(self.f_start + (i * self.f_step))
            # On ne prend que 256 samples pour gagner du temps
            complex_data.append(np.mean(self.hw.rx()[:256]))
        return np.array(complex_data)

    def update(self, frame):
        current_scan = self.get_fast_scan()
        
        if self.prev_scan is None:
            self.prev_scan = current_scan
            return self.line,

        # --- CALCUL DE SENSIBILITÉ PHASE ---
        # On regarde la différence d'angle entre le scan N et N-1
        # C'est beaucoup plus sensible que l'amplitude dans le "bordel"
        phase_diff = np.angle(current_scan * np.conj(self.prev_scan))
        motion_score = np.mean(np.abs(phase_diff))
        
        # On normalise et on applique un petit boost pour la visibilité
        motion_score = np.clip(motion_score * 2, 0, 1)

        self.prev_scan = current_scan

        # Mise à jour graphique
        self.history = np.roll(self.history, -1)
        self.history[-1] = motion_score
        
        # Changement de couleur dynamique (Alerte !)
        color = '#ff0055' if motion_score > 0.15 else '#00ff41'
        self.line.set_ydata(self.history)
        self.line.set_color(color)

        return self.line,

if __name__ == "__main__":
    TurboMotionTrigger()