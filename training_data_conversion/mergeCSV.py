import os
import pandas as pd

def listar_csv_recursivo(carpeta):
    archivos = []
    for raiz, _, archivos_en_raiz in os.walk(carpeta):
        for archivo in archivos_en_raiz:
            if archivo.lower().endswith('.csv'):
                ruta_completa = os.path.join(raiz, archivo)
                ruta_relativa = os.path.relpath(ruta_completa, carpeta)
                archivos.append(ruta_relativa)
    return set(archivos)

def normalizar_columnas(cols):
    # Quitar puntos y espacios para normalizar nombres
    return [col.replace('.', '').replace(' ', '') for col in cols]

def fusionar_csv(csv1_path, csv2_path):
    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)
    # Normalizar columnas para que coincidan
    df1.columns = normalizar_columnas(df1.columns)
    df2.columns = normalizar_columnas(df2.columns)
    # Asegurar orden y nombres iguales
    df2.columns = df1.columns
    # Convertir a int y fusionar con OR
    df1 = df1.astype(int)
    df2 = df2.astype(int)
    df_fusion = (df1 | df2).astype(int)
    return df_fusion

def fusionar_carpetas(carpeta1, carpeta2, carpeta_salida):
    archivos1 = listar_csv_recursivo(carpeta1)
    archivos2 = listar_csv_recursivo(carpeta2)

    archivos_comunes = archivos1.intersection(archivos2)
    print(archivos_comunes)
    
    for archivo_rel in archivos_comunes:
        ruta1 = os.path.join(carpeta1, archivo_rel)
        ruta2 = os.path.join(carpeta2, archivo_rel)
        
        df_fusion = fusionar_csv(ruta1, ruta2)

        if 'Test' in df_fusion.columns:
            df_fusion = df_fusion.drop(columns=['Test'])
        
        # Crear carpeta destino si no existe
        salida_path = os.path.join(carpeta_salida, archivo_rel)
        os.makedirs(os.path.dirname(salida_path), exist_ok=True)
        
        df_fusion.to_csv(salida_path, index=False)
        print(f"Fusionado y guardado: {salida_path}")

# Ejemplo uso:
fusionar_carpetas("JS_annotations", "LL_annotations", "merged_annotations")
