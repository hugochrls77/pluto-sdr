import iio

uri = "usb:1.18.5"

try:
    ctx = iio.Context(uri)
    phy = ctx.find_device("ad9361-phy")
    
    # On cherche dans debug_attrs si attrs a échoué
    if "model" in phy.debug_attrs:
        phy.debug_attrs["model"].value = "ad9364"
        print("Succès ! Modèle forcé via debug_attrs.")
    elif "model" in phy.attrs:
        phy.attrs["model"].value = "ad9364"
        print("Succès ! Modèle forcé via attrs.")
    else:
        print("L'attribut 'model' est introuvable. Voici ce qui est dispo :")
        print(phy.attrs.keys())
        
except Exception as e:
    print(f"Erreur : {e}")