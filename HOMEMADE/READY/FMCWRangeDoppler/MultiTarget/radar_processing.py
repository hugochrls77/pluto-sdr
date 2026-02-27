import numpy as np
from scipy.signal import convolve2d
from scipy.ndimage import label, maximum_position

def cfar_1d(X_k, num_guard_cells, num_ref_cells, bias, cfar_method="average"):
    # (Garde ton code précédent ici sans le modifier)
    N = X_k.size
    cfar_values = np.zeros(X_k.shape)
    for center_index in range(num_guard_cells + num_ref_cells, N - (num_guard_cells + num_ref_cells)):
        min_index = center_index - (num_guard_cells + num_ref_cells)
        min_guard = center_index - num_guard_cells
        max_guard = center_index + num_guard_cells + 1
        max_index = center_index + (num_guard_cells + num_ref_cells) + 1

        lower_nearby = X_k[min_index:min_guard]
        upper_nearby = X_k[max_guard:max_index]

        if cfar_method == "average":
            mean = np.mean(np.concatenate((lower_nearby, upper_nearby)))
        else:
            mean = 0

        cfar_values[center_index] = mean * bias

    targets_only = np.copy(X_k)
    targets_only[X_k < cfar_values] = np.nan
    return cfar_values, targets_only


def cfar_2d(rd_matrix, guard_cells, ref_cells, bias):
    """
    Filtre CFAR 2D optimisé par convolution.
    guard_cells et ref_cells sont des tuples (Range, Doppler).
    """
    gr, gd = guard_cells
    rr, rd = ref_cells
    
    # Taille totale du masque (noyau)
    kr = 2 * (gr + rr) + 1
    kd = 2 * (gd + rd) + 1
    
    kernel = np.ones((kr, kd))
    
    # On évide le centre : la zone de garde et la cellule sous test sont mises à 0
    kernel[rr:rr + 2 * gr + 1, rd:rd + 2 * gd + 1] = 0
    
    # Normalisation pour calculer une moyenne
    kernel /= np.sum(kernel)
    
    # Convolution 2D pour obtenir le plancher de bruit local instantanément
    noise_level = convolve2d(rd_matrix, kernel, mode='same', boundary='symm')
    
    # Calcul du seuil
    threshold = noise_level * bias
    
    # Filtrage
    targets = np.copy(rd_matrix)
    targets[rd_matrix < threshold] = np.nan
    
    return threshold, targets

def extract_targets(cfar_2d_matrix, r_min, r_max, v_min, v_max):
    """
    Extrait les coordonnées physiques (Distance, Vitesse, Puissance) des cibles 
    à partir de la matrice 2D filtrée par le CFAR.
    """
    # 1. Créer un masque binaire où True = Cible détectée (non-NaN)
    detection_mask = ~np.isnan(cfar_2d_matrix)
    
    # 2. Regrouper les pixels adjacents en "îlots" (clusters)
    labeled_array, num_features = label(detection_mask)
    
    # Si rien n'est détecté, on s'arrête là
    if num_features == 0:
        return []
        
    # 3. Trouver le pixel maximum (le pic) pour chaque îlot
    # maximum_position retourne une liste de tuples (index_ligne, index_colonne)
    peaks = maximum_position(
        cfar_2d_matrix, 
        labels=labeled_array, 
        index=np.arange(1, num_features + 1)
    )
    
    # Dimensions de la matrice pour faire la conversion Index -> Physique
    num_r_bins, num_v_bins = cfar_2d_matrix.shape
    
    extracted_targets = []
    
    for r_idx, v_idx in peaks:
        # Conversion de l'index matriciel en valeur physique
        # Interpolation linéaire entre le min et le max
        r_val = r_min + (r_idx / (num_r_bins - 1)) * (r_max - r_min)
        v_val = v_min + (v_idx / (num_v_bins - 1)) * (v_max - v_min)
        
        # Récupération de la puissance (en dB)
        power_dB = 10 * np.log10(cfar_2d_matrix[r_idx, v_idx] + 1e-10)
        
        extracted_targets.append((r_val, v_val, power_dB))
        
    # On trie les cibles par distance croissante pour que ce soit plus lisible
    extracted_targets.sort(key=lambda x: x[0])
        
    return extracted_targets