import numpy as np
import matplotlib.pyplot as plt
from random import uniform
from numpy.fft import fft, fftshift, fft2
from radar_physics import get_radar_params, get_resolutions
from radar_simulator import generate_multi_target_cpi
from radar_processing import cfar_1d, cfar_2d, extract_targets

plt.style.use("ggplot")

def run_multi_target_simulation():
    params = get_radar_params()
    res_range, max_vel, res_vel = get_resolutions(params)
    
    # =========================================================
    # 🛠️ SÉLECTEUR DE SCÉNARIO
    # =========================================================
    SCENARIO = "CLOSE" 
    
    if SCENARIO == "CLASSIC":
        print(">> SCÉNARIO : Classique (Cibles variées)")
        targets = [
            (20, 10, 0), (20, -8, -5), (10, 5, -10), 
            (35, 15, -2), (5, -2, -15), (28, 0, -6)
        ]
    elif SCENARIO == "NEAR_FAR":
        print(">> SCÉNARIO : Near-Far Problem (Le Camion et le Piéton)")
        targets = [
            (5, 0, 25),    
            (30, 12, -20), 
            (35, -5, -10)  
        ]
    elif SCENARIO == "CLOSE":
        print(">> SCÉNARIO : Limite de Résolution (Cibles très proches)")
        targets = [
            (20.0, 10.0, 0),    
            (20.5, 10.5, 0),    
            (10.0, -5.0, 5),    
        ]
    elif SCENARIO == "RANDOM":
        print(">> SCÉNARIO : Chaos Aléatoire")
        num_targets = np.random.randint(5, 9)
        targets = []
        for _ in range(num_targets):
            r = uniform(3, 40)                   
            v = uniform(-max_vel*0.9, max_vel*0.9) 
            p = uniform(-20, 10)                 
            targets.append((r, v, p))

    print("==================================================")
    print("🎯 VÉRITÉS TERRAIN (Ce que l'on simule) :")
    for i, (r, v, p) in enumerate(targets, 1):
        print(f"  Cible {i} : Dist = {r:05.2f} m | Vit = {v:>6.2f} m/s | Pwr = {p:6.1f} dB")
    print("==================================================\n")
    
    N = 10000
    noise_level = 0.8 
    cpi_signal, t, fs = generate_multi_target_cpi(targets, params, N, noise_std=noise_level)

    fft_len = N * 8
    rmax = 3e8 * params['Tc'] * fs / (2 * params['bw'])
    ranges = np.linspace(-rmax / 2, rmax / 2, fft_len)
    
    # --- 1. FFT 1D ---
    X_k_lin = np.abs(fftshift(fft(cpi_signal[0], fft_len))) / (N / 2)
    threshold_1d_lin, targets_1d_lin = cfar_1d(X_k_lin, 50, 100, 3.5, "average")
    X_k_dB = 10 * np.log10(X_k_lin + 1e-10)
    threshold_1d_dB = 10 * np.log10(threshold_1d_lin + 1e-10)
    targets_1d_dB = 10 * np.log10(targets_1d_lin + 1e-10)

    # --- 2. FFT 2D (Avec Fenêtre) ---
    doppler_window = np.blackman(params['M'])
    cpi_windowed_2d = cpi_signal * doppler_window[:, np.newaxis]
    range_doppler_lin = np.abs(fftshift(fft2(cpi_windowed_2d.T))) / (N / 2)
    
    # --- 3. CFAR 2D ---
    guard_cells_2d = (20, 1)
    ref_cells_2d = (40, 3)   
    threshold_2d, targets_2d_lin = cfar_2d(range_doppler_lin, guard_cells_2d, ref_cells_2d, bias=5.5)

    range_doppler_dB = 10 * np.log10(range_doppler_lin + 1e-10)
    targets_2d_dB = 10 * np.log10(targets_2d_lin + 1e-10)

    # --- 4. EXTRACTION (CLUSTERING) ---
    detected_targets = extract_targets(
        targets_2d_lin, 
        r_min=ranges.min(), r_max=ranges.max(), 
        v_min=-max_vel, v_max=max_vel
    )
    
    # --- 5. Visualisation (Grille 2x2) ---
    fig, axs = plt.subplots(2, 2, figsize=(18, 12))
    ax1, ax2 = axs[0, 0], axs[0, 1]
    ax3, ax4 = axs[1, 0], axs[1, 1]

    # --- En haut à gauche : 1D ---
    ax1.plot(ranges, X_k_dB, label="X[k]", color='b') 
    ax1.plot(ranges, threshold_1d_dB, label="Threshold", color='y') 
    ax1.plot(ranges, targets_1d_dB, label="Targets", color='r', linewidth=2.5) 
    ax1.set_xlim([0, 45]) 
    ax1.set_ylim([-45, 30]) 
    ax1.set_title("1D : Profil de distance et CFAR", fontsize=14)
    ax1.set_xlabel("Distance (m)")
    ax1.set_ylabel("Amplitude (dB)")
    ax1.legend(loc="upper right")

    # =========================================================
    # --- NOUVEAU : En haut à droite : VÉRITÉ TERRAIN 2D ---
    # =========================================================
    ax2.set_facecolor('midnightblue') 
    
    # Extraction des coordonnées pour l'affichage idéal
    gt_r = [t[0] for t in targets]
    gt_v = [t[1] for t in targets]
    gt_p = [t[2] for t in targets]
    
    # Affichage avec un nuage de points (scatter)
    sc = ax2.scatter(gt_v, gt_r, c=gt_p, cmap='jet', s=100, edgecolors='white', linewidth=1.5, zorder=5)
    ax2.set_xlim([-max_vel, max_vel])
    ax2.set_ylim([0, 45])
    ax2.set_title("2D : Vérité Terrain (Ce qui est envoyé)", fontsize=14)
    ax2.set_xlabel("Vitesse (m/s)")
    ax2.set_ylabel("Distance (m)")
    fig.colorbar(sc, ax=ax2, fraction=0.046, pad=0.04, label="Puissance relative (dB)")
    
    # Grille fine pour bien lire les coordonnées
    ax2.grid(True, linestyle='--', alpha=0.5)

    # --- En bas à gauche : 2D BRUT ---
    extent = [-max_vel, max_vel, ranges.min(), ranges.max()]
    max_val = np.max(range_doppler_dB)
    
    im3 = ax3.imshow(range_doppler_dB, aspect="auto", extent=extent, origin="lower", 
                     vmax=max_val, vmin=max_val - 40, cmap='jet')
    ax3.set_ylim([0, 45])
    ax3.set_title(f"2D : Range-Doppler BRUT (Bruit={noise_level})", fontsize=14)
    ax3.set_xlabel("Vitesse (m/s)")
    ax3.set_ylabel("Distance (m)")
    fig.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)

    # --- En bas à droite : 2D CFAR & CLUSTERING ---
    ax4.set_facecolor('midnightblue') 
    im4 = ax4.imshow(targets_2d_dB, aspect="auto", extent=extent, origin="lower", 
                     vmax=max_val, vmin=max_val - 40, cmap='jet')
    ax4.set_ylim([0, 45])
    ax4.set_title("2D : Sortie CFAR & Clustering (Ce qui est détecté)", fontsize=14)
    ax4.set_xlabel("Vitesse (m/s)")
    ax4.set_ylabel("Distance (m)")
    
    # Cercles blancs autour des cibles extraites
    for r, v, p in detected_targets:
        if r > 1:
            ax4.plot(v, r, 'wo', markersize=12, markerfacecolor='none', markeredgewidth=1.5)

    fig.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_multi_target_simulation()