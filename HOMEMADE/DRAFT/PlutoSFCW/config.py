# homemade/config.py
IP_ADDRESS = "ip:192.168.2.1"

SAMPLE_RATE = int(2.0e6) 
CENTER_FREQ = int(800e6) 

# Réglages prudents pour le câble SMA
TX_GAIN = -20   
RX_GAIN = 50.0  

FFT_SIZE = 2048 # On reste sur une taille fixe