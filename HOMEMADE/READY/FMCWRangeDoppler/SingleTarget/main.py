import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftshift, fft2
from radar_physics import get_radar_params, get_resolutions
from radar_simulator import generate_cpi_signal

plt.style.use("ggplot")

def run_simulation():
    params = get_radar_params()
    R_target, v_target = 20, 10
    res_range, max_vel, res_vel = get_resolutions(params)
    
    N = 10000
    cpi_signal, t, fs, f_beat, phase_diff = generate_cpi_signal(R_target, v_target, params, N)

    # 3. FFT 1D (Range)
    fft_len = N * 8
    # CORRECTION : Restauration du rmax et de l'axe symétrique pour le fftshift
    rmax = 3e8 * params['Tc'] * fs / (2 * params['bw'])
    ranges = np.linspace(-rmax / 2, rmax / 2, fft_len)
    
    X_k = 10 * np.log10(np.abs(fftshift(fft(cpi_signal[0], fft_len))) / (N / 2))

    # 4. FFT 2D (Range-Doppler)
    rd_map = 10 * np.log10(fftshift(np.abs(fft2(cpi_signal.T))) / (N / 2))

    # 5. Visualisation
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    ax1.plot(ranges, X_k)
    ax1.set_xlim([0, 40]) # On zoome bien du centre vers la droite
    ax1.set_title("Spectre de Distance (1er Chirp)")
    ax1.set_xlabel("Distance (m)")
    ax1.set_ylabel("Magnitude")

    # CORRECTION : Restauration des limites symétriques de distance (Y) pour le fftshift 2D
    extent = [-max_vel, max_vel, ranges.min(), ranges.max()]
    im = ax2.imshow(rd_map, aspect="auto", extent=extent, origin="lower", vmax=2, vmin=-25)
    ax2.set_ylim([0, 40]) # Zoom sur les distances positives
    ax2.set_title("Carte Range-Doppler")
    ax2.set_xlabel("Vitesse (m/s)")
    ax2.set_ylabel("Distance (m)")
    fig.colorbar(im, ax=ax2)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()