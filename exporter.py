import numpy as np
from PIL import Image

class HeightmapExporter:
    """
    Exporta a matriz de altura Z (float) para um arquivo PNG de 16 bits.
    """
    def __init__(self, filename="terrain_heightmap.png"):
        self.filename = filename

    def export_heightmap(self, Z_data, output_path=None):
        """
        Normaliza a matriz Z e salva como um PNG de 16 bits.

        Args:
            Z_data (np.ndarray): Matriz 2D de alturas (floats).
            output_path (str, optional): Caminho completo para salvar o arquivo.
        """
        if output_path is None:
            output_path = self.filename

        print(f"Iniciando exportação para {output_path}...")

        # 1. Normalização dos Dados
        Z_min = Z_data.min()
        Z_max = Z_data.max()

        if Z_max == Z_min:
            print("Erro: Todos os pontos têm a mesma altura. Usando 0.5.")
            normalized_Z = np.ones_like(Z_data) * 0.5
        else:
            normalized_Z = (Z_data - Z_min) / (Z_max - Z_min)

        # 2. Conversão para 16-bit
        max_16bit = 65535
        image_data_16bit = (normalized_Z * max_16bit).astype(np.uint16)

        # 3. Criação e Salvamento da Imagem
        img = Image.fromarray(image_data_16bit, mode='I;16')

        try:
            img.save(output_path)
            print(f"Sucesso! Heightmap 16-bit salvo em: {output_path}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")
