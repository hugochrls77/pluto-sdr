import numpy as np
from random import randint
import matplotlib.pyplot as plt
from scipy import signal
from scipy.constants import c, pi, mph
from numpy.fft import fft, fftshift, fft2
from matplotlib import cm

plt.style.use("ggplot")

t = np.linspace(0, 1, 1000)
f = 3
range_shift = -pi / 3
doppler_shift = 0.1
tx = (signal.sawtooth(2 * pi * f * t, width=0.5) + 1) / 2
rx = (signal.sawtooth(2 * pi * f * t + range_shift, width=0.5) + 1) / 2 + doppler_shift
if_sig = np.abs(tx - rx)


fig, ax = plt.subplots(2, 1, figsize=(16, 6), layout="constrained")
fig.suptitle(
    "Disambiguating Range and Velocity with a Triangular LFM\n(only for single target)",
    fontsize=20,
)
ax[0].set_ylabel("Frequency (Hz)", fontsize=16)
ax[0].set_title("Transmit and Received Frequency Ramps", fontsize=16)
ax[0].plot(t, tx, label="Tx", c="b")
ax[0].plot(t, rx, label="Rx", c="r")
ax[1].set_ylim([0, 0.6])
ax[1].set_ylabel(r"$f_{IF}$ (Hz)", fontsize=16)
ax[1].set_xlabel("Time (s)", fontsize=16)
ax[1].set_title("Mixer Output", fontsize=16)
ax[1].text(0.08, 0.3, r"$f_{beat} - f_d$", fontsize=18)
ax[1].text(0.25, 0.5, r"$f_{beat} + f_d$", fontsize=18)
ax[1].plot(t, if_sig, label="Rx", c="orange")
plt.show()