# main.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Import de nos modules
import config as cfg
from sdr_device import PlutoDevice
from processor_microdoppler import MicroDopplerProcessor

def main():
    # --- 1. Initialisation Matérielle et Algorithmique ---
    sdr = PlutoDevice(fs=cfg.FS, lo=cfg.LO_FREQ)
    sdr.transmit_cw()
    
    processor = MicroDopplerProcessor(
        nfft=cfg.NFFT, 
        decimation=cfg.DECIMATION, 
        mti_alpha=cfg.MTI_ALPHA
    )

    # --- 2. Préparation de l'Interface Graphique ---
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#111111')
    ax.set_facecolor('#111111')
    
    ax.set_title("Radar Micro-Doppler : Signature de pales (Drone/Ventilateur)", color='white', pad=15)
    ax.set_xlabel("Vitesse Radiale (m/s)", color='white')
    ax.set_ylabel("Temps (Frames)", color='white')
    ax.tick_params(colors='white')

    # Calcul des limites physiques pour les axes de Matplotlib
    max_doppler_freq = cfg.EFFECTIVE_FS / 2
    max_velocity = (max_doppler_freq * cfg.C) / (2 * cfg.LO_FREQ)
    print(f"[INFO] Vitesse théorique max mesurable : +/- {max_velocity:.2f} m/s")

    # Création de la matrice d'affichage
    waterfall_data = np.zeros((cfg.HISTORY_SIZE, cfg.NFFT))
    
    # Configuration de l'image (RTI Heatmap)
    cax = ax.imshow(waterfall_data, aspect='auto', cmap='jet', 
                    origin='lower', extent=[-max_velocity, max_velocity, cfg.HISTORY_SIZE, 0])
    
    # Limiter l'affichage à des vitesses réalistes pour un drone (+/- 25 m/s)
    ax.set_xlim(-cfg.MAX_DISPLAY_VELOCITY, cfg.MAX_DISPLAY_VELOCITY)
    ax.axvline(0, color='white', linestyle='--', alpha=0.2) # Ligne de vitesse zéro

    # Barre de couleurs
    cbar = fig.colorbar(cax, ax=ax)
    cbar.set_label("Puissance relative (dB)", color='white')
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

    # --- 3. Boucle Temps Réel ---
    def update(frame):
        nonlocal waterfall_data
        
        # Capture et Traitement
        rx_sig = sdr.receive_signal(cfg.SAMPLES)
        mag_db = processor.process_stft(rx_sig)
        
        # Décalage de la matrice (Effet Waterfall descendant)
        waterfall_data = np.roll(waterfall_data, -1, axis=0)
        waterfall_data[-1, :] = mag_db
        
        cax.set_array(waterfall_data)
        
        # Ajustement dynamique du contraste (Coupe le bruit de fond)
        vmin = np.percentile(waterfall_data, 60) # On ignore les 60% de signaux les plus faibles
        vmax = np.max(waterfall_data)
        cax.set_clim(vmin=vmin, vmax=vmax)
        
        return cax,

    # Interval de 50ms = ~20 images par seconde
    ani = FuncAnimation(fig, update, frames=200, interval=50, blit=True)
    
    try:
        plt.tight_layout()
        plt.show()
    except KeyboardInterrupt:
        print("\n[INFO] Fermeture demandée par l'utilisateur.")
    finally:
        sdr.stop()

if __name__ == "__main__":
    main()