# signals.py
import numpy as np

def generate_sine_wave(fs, duration=1.0, freq=500000):
    """Génère une onde pure décalée de 'freq' Hz"""
    t = np.linspace(0, duration, int(fs*duration))
    # Exp(jwt) = Rotation pure = Fréquence unique
    signal = np.exp(1j * 2 * np.pi * freq * t)
    return signal

def generate_fm_siren(fs, duration=1.0):
    """Génère une sirène de police modulée en FM"""
    t = np.linspace(0, duration, int(fs*duration))
    # Audio : Oscillation lente (5 Hz)
    audio = np.sin(2 * np.pi * 5 * t) 
    # Modulation FM (Largeur 75 kHz)
    f_dev = 75000
    signal = np.exp(1j * 2 * np.pi * f_dev * np.cumsum(audio) / fs)
    return signal

def generate_qpsk(fs, num_symbols=1000):
    """Génère un nuage de points QPSK (4 états)"""
    # Bits aléatoires
    bits = np.random.randint(0, 2, num_symbols*2)
    
    symbols = []
    for i in range(0, len(bits), 2):
        b1, b2 = bits[i], bits[i+1]
        # Mapping : 0->1, 1->-1
        symbols.append(complex(1 if b1==0 else -1, 1 if b2==0 else -1))
    
    # Répétition pour donner de l'épaisseur temporelle (Samples per Symbol)
    sps = 16
    iq = np.repeat(symbols, sps)
    return iq