import numpy as np

def get_continent_centers(count):
    """Retorna coordenadas normalizadas (0 a 1) para N continentes."""
    if count == 1: return [(0.5, 0.5)]
    if count == 2: return [(0.3, 0.5), (0.7, 0.5)]
    if count == 3: return [(0.5, 0.28), (0.25, 0.72), (0.75, 0.72)]
    if count == 4: return [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]
    if count == 5: return [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75), (0.5, 0.5)]
    return [(0.5, 0.5)]

def generate_multi_point_mask(shape, centers, size_factor=0.3, softness=0.15):

    h, w = shape
    y, x = np.ogrid[:h, :w]
    final_mask = np.zeros(shape)
    
    dist_center = np.sqrt((x - w/2)**2 + (y - h/2)**2) / (max(h, w)/2)

    global_safety = 1.0 - np.clip((dist_center - 0.9) / 0.1, 0, 1)

    for (cx_norm, cy_norm) in centers:
        cx, cy = cx_norm * w, cy_norm * h
        dist = np.sqrt((x - cx)**2 + (y - cy)**2) / max(h, w)
        
        mask = 1.0 - np.clip((dist - size_factor) / softness, 0, 1)
        final_mask = np.maximum(final_mask, mask)
        
    return final_mask * global_safety