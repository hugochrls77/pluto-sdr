# stop_tx.py
import adi
import config as cfg

print(f"Connexion au Pluto ({cfg.IP_ADDRESS})...")
sdr = adi.Pluto(cfg.IP_ADDRESS)

print("🛑 Arrêt de l'émission...")
sdr.tx_destroy_buffer() # C'est cette commande qui vide la mémoire et coupe l'ampli TX

print("Le Pluto est silencieux.")
del sdr