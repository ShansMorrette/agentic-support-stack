import os

# Configuración
FRONTEND_DIR = r"d:\01-A L2 Projecto\Sas Agente\agentic-support-stack\frontend\app"
FILES_TO_UPDATE = [
    os.path.join(FRONTEND_DIR, "main.py"),
    os.path.join(FRONTEND_DIR, "pages", "login.py"),
    os.path.join(FRONTEND_DIR, "pages", "dashboard.py"),
]
OLD_DEFAULT = "http://127.0.0.1:8001"
# El usuario solicitó http://app:8001 (nombre del servicio en Docker)
NEW_DEFAULT = "http://app:8001"

def update_backend_url():
    for file_path in FILES_TO_UPDATE:
        if not os.path.exists(file_path):
            print(f"Error: No se encontro {file_path}")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Reemplazo robusto para BACKEND_URL = os.getenv("BACKEND_URL", "...")
        target = f'os.getenv("BACKEND_URL", "{OLD_DEFAULT}")'
        replacement = f'os.getenv("BACKEND_URL", "{NEW_DEFAULT}")'
        
        if target in content:
            new_content = content.replace(target, replacement)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"SUCCESS: URL actualizada en {file_path}")
        elif NEW_DEFAULT in content:
            print(f"INFO: {file_path} ya tiene la URL correcta.")
        else:
            print(f"WARNING: No se encontro el patron esperado en {file_path}")

if __name__ == "__main__":
    update_backend_url()
