# HOMEMADE/DRAFT/PlutoSFCW/motion_trigger.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys, os
import time

sys.path.append(os.path.abspath("../../READY/PlutoDoppler"))
from sdr_device import PlutoDevice

class MotionTrigger:
    def __init__(self):
        # Paramètres rapides pour le mouvement
        self.f_start, self.f_step, self.n_steps = 2_100_000_000, 10_000_000, 30
        self.threshold = 0.05 # Seuil de sensibilité (à ajuster)
        
        self.hw = PlutoDevice(fs=2_000_000, lo=self.f_start)
        self.hw.set_tx_gain('manual', -50)
        self.hw.set_rx_gain('manual', 30)
        
        self.reference_scan = None
        self.history = [] # Pour voir l'évolution du mouvement

        # Interface
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.line, = self.ax.plot([], [], color='#00ff41', lw=2)
        self.ax.set_ylim(0, 0.5)
        self.ax.set_xlim(0, 100)
        self.ax.set_title("DÉTECTEUR DE MOUVEMENT VOLUMÉTRIQUE (SFCW)", color='cyan')
        self.ax.set_ylabel("Indice de changement", fontsize=10)
        self.ax.axhline(self.threshold, color='red', linestyle='--', label="Seuil d'alerte")
        self.ax.legend()

        self.hw.tx(np.ones(1024, dtype=complex) * 0.3)
        self.ani = FuncAnimation(self.fig, self.update, interval=100)
        plt.show()

    def get_quick_scan(self):
        complex_data = []
        for i in range(self.n_steps):
            self.hw.set_lo(self.f_start + (i * self.f_step))
            # On réduit le temps d'attente pour être plus réactif
            complex_data.append(np.mean(self.hw.rx()))
        return np.array(complex_data)

    def update(self, frame):
        current_scan = self.get_quick_scan()
        
        if self.reference_scan is None:
            self.reference_scan = current_scan
            return self.line,

        # Calcul de la différence vectorielle (Mouvement)
        diff = np.abs(current_scan - self.reference_scan)
        motion_score = np.mean(diff) # Score global de changement dans la pièce

        # Mise à jour lente de la référence (pour s'adapter à la dérive thermique)
        self.reference_scan = self.reference_scan * 0.9 + current_scan * 0.1

        self.history.append(motion_score)
        if len(self.history) > 100: self.history.pop(0)

        # Alerte visuelle
        color = '#ff0055' if motion_score > self.threshold else '#00ff41'
        self.line.set_data(range(len(self.history)), self.history)
        self.line.set_color(color)

        return self.line,

if __name__ == "__main__":
    MotionTrigger()