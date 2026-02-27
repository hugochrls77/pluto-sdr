import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from sdr_device import PlutoDevice
from signal_generator import generate_fmcw_chirp
from processor_wall import WallProcessor

# --- PARAMÈTRES ---
C = 3e8
FS = 10_000_000           # 10 MSPS
LO_FREQ = 900_000_000     # 900 MHz
BW = 8_000_000            # Largeur de bande
SWEEP_TIME = 1e-3         
SAMPLES = int(FS * SWEEP_TIME)

# --- AFFICHAGE ---
HISTORY_SIZE = 150        # Nombre de lignes dans le waterfall (environ 7-10 secondes d'historique)

def main():
    sdr = PlutoDevice(fs=FS, lo=LO_FREQ)
    tx_chirp = generate_fmcw_chirp(FS, SWEEP_TIME, BW)
    sdr.transmit_signal(tx_chirp)
    processor = WallProcessor()

    # --- PHASE DE CALIBRATION ---
    print("\n" + "="*50)
    print("⚠️  PHASE DE CALIBRATION - THROUGH-WALL ⚠️")
    print("="*50)
    print("Veuillez vous écarter des antennes.")
    for i in range(5, 0, -1):
        print(f"Calibration dans {i} secondes...")
        time.sleep(1)

    print("\n[CALIBRATION] Enregistrement de l'empreinte du mur en cours... NE BOUGEZ PAS.")
    empty_profiles = []
    for _ in range(50):
        rx_sig = sdr.receive_signal(SAMPLES)
        prof = processor.process_fmcw_aligned(tx_chirp, rx_sig)
        empty_profiles.append(prof)
    processor.calibrate(empty_profiles)
    print("✅ Calibration terminée. Vous pouvez vous placer derrière l'obstacle.\n")


    # --- INTERFACE GRAPHIQUE RTI ---
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    
    ax.set_title("Radar RTI : Détection des Mouvements à travers le mur", color='white', pad=15)
    ax.set_xlabel("Distance (Mètres)", color='white') # <--- Changé ici
    ax.set_ylabel("Temps (Historique)", color='white')
    ax.tick_params(colors='white')

    waterfall_data = np.zeros((HISTORY_SIZE, processor.nfft // 2))
    
    # --- CALCUL DE LA DISTANCE MAXIMALE ---
    max_beat_freq = FS / 2
    max_distance = (max_beat_freq * C * SWEEP_TIME) / (2 * BW)
    
    # On utilise 'extent' pour dire à l'image que l'axe X va de 0 à max_distance
    cax = ax.imshow(waterfall_data, aspect='auto', cmap='inferno', 
                    origin='lower', extent=[0, max_distance, HISTORY_SIZE, 0])
    
    # On limite l'affichage aux 15 premiers mètres (pour mieux voir à travers un mur !)
    ax.set_xlim(0, 15)
    
    # Ajout de l'échelle de couleurs
    cbar = fig.colorbar(cax, ax=ax)
    cbar.set_label("Intensité du mouvement (Linéaire)", color='white')
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

    def update(frame):
        nonlocal waterfall_data
        
        # 1. Capture et Traitement
        rx_sig = sdr.receive_signal(SAMPLES)
        complex_prof = processor.process_fmcw_aligned(tx_chirp, rx_sig)
        dynamic_mag = processor.get_dynamic_signal(complex_prof)
        
        # 2. Décalage de l'image vers le bas (effet Waterfall)
        waterfall_data = np.roll(waterfall_data, -1, axis=0)
        waterfall_data[-1, :] = dynamic_mag
        
        # 3. Mise à jour de l'affichage
        cax.set_array(waterfall_data)
        
        # Auto-ajustement des couleurs pour faire ressortir les pics
        max_val = np.max(waterfall_data) + 1 # +1 pour éviter division par zéro
        cax.set_clim(vmin=0, vmax=max_val * 0.8) # 0.8 permet de saturer légèrement les gros échos
        
        return cax,

    ani = FuncAnimation(fig, update, frames=200, interval=50, blit=True)
    
    try:
        plt.tight_layout()
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        sdr.stop()

if __name__ == "__main__":
    main()