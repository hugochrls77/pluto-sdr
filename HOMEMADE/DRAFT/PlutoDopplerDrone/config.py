# config.py

# --- Constantes Physiques ---
C = 3e8                        # Vitesse de la lumière (m/s)
LO_FREQ = 5_800_000_000        # Fréquence d'émission (5.8 GHz)

# --- Paramètres du SDR ---
FS = 1_000_000                 # Échantillonnage matériel (1 MSPS)
DECIMATION = 100               # Facteur de décimation (Zoom temporel)
EFFECTIVE_FS = FS / DECIMATION # Fréquence d'échantillonnage après décimation (10 kHz)

# --- Paramètres de Traitement ---
NFFT = 1024                    # Taille de la transformée de Fourier
SAMPLES = NFFT * DECIMATION    # Nombre d'échantillons à capturer par itération (ex: 102400)
MTI_ALPHA = 0.05               # Agressivité du filtre d'effacement du fond (0 = off, 1 = max)

# --- Paramètres d'Affichage ---
HISTORY_SIZE = 150             # Nombre de lignes dans la cascade (Waterfall)
MAX_DISPLAY_VELOCITY = 25      # Limite de l'axe X de l'affichage (en m/s)