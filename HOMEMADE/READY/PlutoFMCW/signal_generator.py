git import numpy as np

class SignalGenerator:
    @staticmethod
    def generate(sig_type, freq, fs, num_samples=4096):
        t = np.arange(num_samples) / fs
        if sig_type == 'Sinus':
            return np.exp(1j * 2 * np.pi * freq * t)
        elif sig_type == 'Carré':
            return np.sign(np.cos(2*np.pi*freq*t)) + 1j*np.sign(np.sin(2*np.pi*freq*t))
        elif sig_type == 'Triangle':
            return (2*np.abs(2*(t*freq-np.floor(t*freq+0.5)))-1) + 1j*(2*np.abs(2*(t*freq-np.floor(t*freq+0.25)))-1)
        elif sig_type == 'Scie':
            return 2*(t*freq - np.floor(0.5 + t*freq)) + 1j*2*(t*freq - np.floor(0.25 + t*freq))
        elif sig_type == 'Bruit':
            return (np.random.randn(num_samples) + 1j*np.random.randn(num_samples)) / 3
        elif sig_type == 'QPSK_Raw':
            sps = 8 
            num_symbols = num_samples // sps
            symbols = np.array([1+1j, -1+1j, -1-1j, 1-1j]) / np.sqrt(2)
            bits = np.random.randint(0, 4, num_symbols)
            iq_upsampled = np.repeat(symbols[bits], sps)
            return iq_upsampled[:num_samples]
        elif sig_type == 'QPSK_Filtered':
            sps = 8 
            num_symbols = num_samples // sps
            symbols = np.array([1+1j, -1+1j, -1-1j, 1-1j]) / np.sqrt(2)
            bits = np.random.randint(0, 4, num_symbols)
            iq_upsampled = np.repeat(symbols[bits], sps)
            kernel = np.ones(sps) / sps
            return np.convolve(iq_upsampled, kernel, mode='same')[:num_samples]
        return np.zeros(num_samples)
    
    def generate_chirp(fs, duration_samples, bw):
        t = np.arange(duration_samples) / fs
        # f(t) monte de -bw/2 à +bw/2
        k = bw / (duration_samples / fs) # Pente du chirp
        chirp = np.exp(1j * np.pi * k * t**2)
        return chirp.astype(np.complex64)