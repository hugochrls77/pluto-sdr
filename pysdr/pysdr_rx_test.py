import numpy as np
import adi

sample_rate = 1e6 # Hz
center_freq = 400e6 # Hz
num_samps = 10000 # number of samples returned per call to rx()

sdr = adi.Pluto('usb:1.4.5')
sdr.gain_control_mode_chan0 = 'fast_attack'
sdr.rx_hardwaregain_chan0 = 70.0 # dB
sdr.rx_lo = int(center_freq)
sdr.sample_rate = int(sample_rate)
sdr.rx_rf_bandwidth = int(sample_rate) # filter width, just set it to the same as sample rate for now
sdr.rx_buffer_size = num_samps

samples = sdr.rx() # receive samples off Pluto
print(samples[0:10])