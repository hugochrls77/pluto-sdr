# 🧱 Détection "Through-Wall" (À travers le mur) avec PlutoSDR

Ce projet implémente un système radar expérimental capable de détecter des micro-mouvements humains (comme la respiration ou le déplacement) situés derrière un obstacle opaque (mur en plâtre, brique, béton) en utilisant un ADALM-Pluto (SDR).

Il est inspiré des travaux de recherche sur la détection humaine UWB/FMCW en environnements encombrés.

## 🔬 Théorie et Physique du Radar

La détection à travers les murs présente un défi physique majeur : le mur agit comme un miroir massif. L'écho du mur masque complètement le minuscule écho du corps humain situé derrière. 

Pour contourner ce problème, cette architecture repose sur 3 piliers :
1. **Fréquence de pénétration (900 MHz) :** Au lieu des 5.8 GHz habituels (qui rebondissent), le Pluto est configuré à 900 MHz. Cette plus grande longueur d'onde permet de traverser la matière solide avec moins d'atténuation.
2. **Modulation FMCW :** L'émission d'un *Chirp* (rampe de fréquence) large bande permet de discriminer les échos en fonction de leur distance matérielle.
3. **Annulation de fond (Clutter Removal) :** Un filtre MTI (Moving Target Indicator) agressif couplé à une phase de **calibration à vide** est utilisé pour soustraire l'empreinte mathématique statique du mur. Ne restent alors que les variations de phase dynamiques causées par la cible.

## 📂 Architecture Logicielle

Le projet est découpé en 4 modules spécialisés :
* `sdr_device.py` : Pilote matériel du PlutoSDR (Gain ajusté, Fréquence LO forcée à 900 MHz).
* `signal_generator.py` : Génération mathématique du signal FMCW (Chirp linéaire).
* `processor_wall.py` : Le "cerveau". Gère la FFT, l'enregistrement de la calibration et le lissage du signal dynamique via moyenne exponentielle glissante.
* `main.py` : Interface utilisateur avec animation Matplotlib en temps réel et orchestration de la séquence de test.

## 🚀 Guide d'Utilisation (Protocole de Test)

⚠️ **ATTENTION : La procédure de lancement est stricte pour garantir le fonctionnement du filtre MTI.**

1. **Placement :** Placez les antennes TX et RX du PlutoSDR face au mur à travers lequel vous souhaitez détecter. Séparez un peu les deux antennes pour éviter les interférences directes.
2. **Lancement :** Exécutez le script principal :
   ```bash
   python main.py