from numpy.fft import fft, fftshift
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.constants import pi
from numpy.lib.stride_tricks import sliding_window_view
import warnings

## ===================================================
## INITIALISATIONS
## ===================================================

plt.style.use("ggplot")
warnings.filterwarnings("ignore")

stop_time = 16 # s
fs = 1000 # Hz
N = fs * stop_time
t = np.linspace(0, stop_time, N)

# Noise generation
noise_mu = 0
noise_sigma_db = -10 # dB
noise_sigma = 10 ** (noise_sigma_db / 10)

np.random.seed(0)
noise = np.random.normal(loc=noise_mu, scale=noise_sigma, size=t.size)

# Signal generation
f1 = 1.5 # Hz
f2 = 2.7 # Hz
f_3 = 3.7 # Hz
power_norm_1 = -6 # dB
power_norm_2 = -9 # dB
power_norm_3 = 0 # dB
A_1 = 10 ** (power_norm_1 / 10)
A_2 = 10 ** (power_norm_2 / 10)
A_3 = 10 ** (power_norm_3 / 10)


x_n = (
    A_1 * np.sin(2 * pi * f1 * t)
    + A_2 * np.sin(2 * pi * f2 * t)
    + A_3 * np.sin(2 * pi * f_3 * t)
    + noise
) / (A_1 + A_2 + A_3 + noise_sigma)

## ===================================================
## POST TREATMENT
## ===================================================

blackman_window = signal.windows.blackman(N)
x_n_windowed = x_n * blackman_window

# FFT
fft_len = N * 4 # do some FFT padding for a smoother output

X_k = fftshift(fft(x_n_windowed, fft_len))
X_k /= N / 2
X_k = np.abs(X_k)
X_k_log = 10 * np.log10(X_k)

freq = np.linspace(-fs / 2, fs / 2, fft_len)

## ===================================================
## CFAR FILTER
## ===================================================

def cfar(X_k, num_guard_cells, num_ref_cells, bias, cfar_method="average"):
    N = X_k.size
    cfar_values = np.zeros(X_k.shape)
    for center_index in range(
        num_guard_cells + num_ref_cells, N - (num_guard_cells + num_ref_cells)
    ):
        min_index = center_index - (num_guard_cells + num_ref_cells)
        min_guard = center_index - num_guard_cells
        max_index = center_index + (num_guard_cells + num_ref_cells) + 1
        max_guard = center_index + num_guard_cells + 1

        lower_nearby = X_k[min_index:min_guard]
        upper_nearby = X_k[max_guard:max_index]

        lower_mean = np.mean(lower_nearby)
        upper_mean = np.mean(upper_nearby)

        if cfar_method == "average":
            mean = np.mean(np.concatenate((lower_nearby, upper_nearby)))
        elif cfar_method == "greatest":
            mean = max(lower_mean, upper_mean)
        elif cfar_method == "smallest":
            mean = min(lower_mean, upper_mean)
        else:
            mean = 0

        output = mean * bias
        cfar_values[center_index] = output

    targets_only = np.copy(X_k)
    targets_only[np.where(X_k < cfar_values)] = np.ma.masked

    return cfar_values, targets_only

threshold, targets_only = cfar(X_k, num_guard_cells=8, num_ref_cells=12, bias=1)

## ===================================================
## GRAPHS PLOT
## ===================================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
fig.subplots_adjust(hspace=0.4) # Espace entre les deux graphes

ax1.plot(t, x_n, label="Signal Original", alpha=0.5)
ax1.plot(t, x_n_windowed, label="Signal Fenêtré (Blackman)", color='tab:blue')
ax1.set_title("Vue complète du signal")
ax1.set_xlabel("Temps (s)")
ax1.set_ylabel("Amplitude")
ax1.legend()

ax2.plot(t, x_n, label="Signal Original", alpha=0.5)
ax2.plot(t, x_n_windowed, label="Signal Fenêtré", color='tab:blue')
ax2.set_title("Zoom sur l'atténuation du fenêtrage (0s à 2s)")
ax2.set_xlabel("Temps (s)")
ax2.set_ylabel("Amplitude")
ax2.set_xlim(6, 10) 
ax2.legend()

plt.figure(2, figsize=(10, 6))
plt.plot(freq, X_k_log, label="X[k]", c="b")
plt.plot(freq, 10 * np.log10(np.abs(threshold)), label="Threshold", c="y")
plt.plot(freq, 10 * np.log10(np.abs(targets_only)), label="Targets", c="r")
plt.xlim(0, 5)
plt.ylim(-50, 0)
plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
plt.title("X[k] with CFAR Threshold and Classified Targets")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude (dB)")

plt.show()