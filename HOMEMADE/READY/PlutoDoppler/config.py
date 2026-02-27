# PlutoDoppler/config.py
class RadarConfig:
    FS = 600_000
    FC = 2_100_000_000
    C = 299792458
    LAMBDA = C / FC
    
    BUFFER_SIZE = 65536 
    FFT_RESOLVED = 131072 
    
    N_HISTORY = 120      
    WATERFALL_RES = 600 
    
    UPDATE_MS = 50       
    
    # --- PARAMÈTRES DE DÉTECTION ---
    DETECTION_MARGIN = 30   # Le pic doit être 6dB au dessus du SQL pour déplacer le curseur
    V_LIMIT = 4.0        
    HZ_LIMIT = 5000      
    DB_MIN = -115        
    DB_MAX = -30