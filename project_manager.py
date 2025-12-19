import pickle
import os

LAST_PROJECT_FILE = ".last_project_path"

class ProjectManager:
    @staticmethod
    def save_project(file_path, data):
        """Salva todos os dados do projeto em um arquivo binário."""
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            ProjectManager.set_last_project_path(file_path)
            return True
        except Exception as e:
            print(f"Erro ao salvar projeto: {e}")
            return False

    @staticmethod
    def load_project(file_path):
        """Carrega os dados do projeto."""
        try:
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            ProjectManager.set_last_project_path(file_path)
            return data
        except Exception as e:
            print(f"Erro ao carregar projeto: {e}")
            return None

    @staticmethod
    def get_last_project_path():
        if os.path.exists(LAST_PROJECT_FILE):
            with open(LAST_PROJECT_FILE, 'r') as f:
                path = f.read().strip()
                return path if os.path.exists(path) else None
        return None

    @staticmethod
    def set_last_project_path(path):
        with open(LAST_PROJECT_FILE, 'w') as f:
            f.write(path)