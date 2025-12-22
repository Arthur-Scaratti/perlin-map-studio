import numpy as np

def get_continent_centers(count):
    """Retorna coordenadas normalizadas (0 a 1) para N continentes."""
    if count == 1:
        return [(0.5, 0.5)]
    elif count == 2:
        return [(0.3, 0.5), (0.7, 0.5)]
    elif count == 3:
        return [(0.5, 0.25), (0.25, 0.75), (0.75, 0.75)]
    elif count == 4:
        return [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]
    elif count == 5:
        return [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75), (0.5, 0.5)]
    return [(0.5, 0.5)]

def generate_multi_point_mask(shape, centers, radius=0.25, softness=0.15):
    """Gera uma máscara suave baseada em centros de massa."""
    h, w = shape
    y, x = np.ogrid[:h, :w]
    final_mask = np.zeros(shape)

    for (cx_norm, cy_norm) in centers:
        cx, cy = cx_norm * w, cy_norm * h
        # Distância Euclidiana
        dist = np.sqrt((x - cx)**2 + (y - cy)**2)
        # Normaliza distância pelo tamanho do mapa
        dist_norm = dist / max(h, w)
        
        # Smoothstep invertido para criar o decaimento suave
        # Onde dist < radius, valor é alto. Onde dist > radius + softness, valor é 0.
        mask = 1.0 - np.clip((dist_norm - radius) / softness, 0, 1)
        # Usamos o máximo para fundir os continentes se eles se encostarem
        final_mask = np.maximum(final_mask, mask)
        
    return final_mask