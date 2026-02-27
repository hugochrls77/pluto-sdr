import iio

# On se connecte avec l'adresse USB que tu as trouvée tout à l'heure
ctx = iio.Context("usb:1.11.5")
ctrl = ctx.find_device("ad9361-phy")

# Cette fonction va envoyer les commandes au "cerveau" du Pluto
def set_burn_attr(attr, value):
    try:
        # On écrit dans les variables d'environnement du firmware
        ctx.set_config_label(attr, value)
        print(f"Propriété {attr} fixée à {value}")
    except Exception as e:
        print(f"Erreur sur {attr}: {e}")

print("Déblocage de la plage de fréquences (70MHz - 6GHz)...")

# On envoie les 3 commandes magiques
set_burn_attr("attr_name", "compatible")
set_burn_attr("attr_val", "ad9364")
set_burn_attr("ad7291_probe", "1")

print("\nC'est fait ! Le Pluto va maintenant redémarrer.")
print("Attends environ 30 secondes que la LED clignote à nouveau.")

# Commande de redémarrage
try:
    # On demande au Pluto de sauvegarder et rebooter
    # Note : Sur certaines versions, il faut le débrancher/rebrancher manuellement
    print("Débranche et rebranche ton Pluto maintenant pour valider.")
except:
    pass