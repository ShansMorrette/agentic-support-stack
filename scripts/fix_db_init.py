import os

# Configuración
DATABASE_FILE_PATH = r"d:\01-A L2 Projecto\Sas Agente\agentic-support-stack\backend\app\infrastructure\database.py"

def fix_database_imports():
    if not os.path.exists(DATABASE_FILE_PATH):
        print(f"Error: No se encontro {DATABASE_FILE_PATH}")
        return

    with open(DATABASE_FILE_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    modified = False

    for line in lines:
        if "from sqlalchemy import insert, select" in line:
            new_lines.append("from sqlalchemy import select\n")
            new_lines.append("from sqlalchemy.dialects.postgresql import insert\n")
            modified = True
        else:
            new_lines.append(line)

    if modified:
        with open(DATABASE_FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"SUCCESS: Importacion corregida en {DATABASE_FILE_PATH}")
    else:
        # Verificar si ya esta corregido
        already_fixed = any("from sqlalchemy.dialects.postgresql import insert" in l for l in lines)
        if already_fixed:
            print("INFO: La importacion ya estaba corregida.")
        else:
            print("WARNING: No se encontro la linea de importacion esperada.")

if __name__ == "__main__":
    fix_database_imports()
