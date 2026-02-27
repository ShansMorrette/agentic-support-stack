import os
import re

# Configuración
FRONTEND_DIR = r"d:\01-A L2 Projecto\Sas Agente\agentic-support-stack\frontend\app"
DASHBOARD_PATH = os.path.join(FRONTEND_DIR, "pages", "dashboard.py")
MAIN_PATH = os.path.join(FRONTEND_DIR, "main.py")
TARGET_TZ = "America/Caracas"

def apply_date_conversion():
    # 1. Modificar dashboard.py
    if os.path.exists(DASHBOARD_PATH):
        with open(DASHBOARD_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Conversión en DataFrame (Gráfico)
        old_df_conv = "df['created_at'] = pd.to_datetime(df['created_at'])"
        new_df_conv = "df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('America/Caracas')"
        
        # Conversión en bucle de historial
        old_loop_conv = "pd.to_datetime(h['created_at']).strftime('%Y-%m-%d %H:%M')"
        new_loop_conv = "pd.to_datetime(h['created_at']).tz_convert('America/Caracas').strftime('%Y-%m-%d %H:%M')"
        
        modified = False
        if old_df_conv in content:
            content = content.replace(old_df_conv, new_df_conv)
            modified = True
        
        if old_loop_conv in content:
            content = content.replace(old_loop_conv, new_loop_conv)
            modified = True
            
        if modified:
            with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"SUCCESS: dashboard.py actualizado con conversion a {TARGET_TZ}")
        else:
            print("INFO: No se encontraron patrones para actualizar en dashboard.py o ya estan aplicados.")

    # 2. Modificar main.py (Panel de Control Inteligente)
    if os.path.exists(MAIN_PATH):
        with open(MAIN_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # En main.py, prospects y tickets se cargan como listas de dicts
        # Necesitamos inyectar la conversion antes de mostrarlos como dataframes
        
        # Localizar donde se crean los DataFrames de prospects y tickets en main.py
        p_pattern = "df_p = pd.DataFrame(prospects)"
        t_pattern = "df_t = pd.DataFrame(tickets)"
        
        # Inyectar conversion
        new_p = "df_p = pd.DataFrame(prospects)\n                if 'created_at' in df_p.columns:\n                    df_p['created_at'] = pd.to_datetime(df_p['created_at']).dt.tz_convert('America/Caracas')"
        new_t = "df_t = pd.DataFrame(tickets)\n                if 'created_at' in df_t.columns:\n                    df_t['created_at'] = pd.to_datetime(df_t['created_at']).dt.tz_convert('America/Caracas')"
        
        modified = False
        if p_pattern in content and 'tz_convert' not in content:
            content = content.replace(p_pattern, new_p)
            modified = True
        
        if t_pattern in content and 'tz_convert' not in content:
            content = content.replace(t_pattern, new_t)
            modified = True
            
        if modified:
            with open(MAIN_PATH, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"SUCCESS: main.py actualizado con conversion a {TARGET_TZ}")
        else:
            print("INFO: No se encontraron patrones para actualizar en main.py o ya estan aplicados.")

if __name__ == "__main__":
    apply_date_conversion()
