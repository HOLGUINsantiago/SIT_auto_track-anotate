import os
import pandas as pd

# Ruta base donde están los archivos CSV
base_dir = r'D:\LBN\Maternal_nest_classification_T_deepethogram\DATA'

# Lista de comportamientos a eliminar
comportamientos_a_eliminar = ["ABN","Carryingpups","Selfgrooming","Eat_drink","Kicking","Groomingpups","Build"]

# Recorrer todos los archivos
for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith('_labels.csv'):
            file_path = os.path.join(root, file)

            # Cargar CSV
            df = pd.read_csv(file_path)

            # Quitar la columna de índice si es necesario
            if df.columns[0] in ['Unnamed: 0', '']:
                df = df.iloc[:, 1:]

            # Eliminar columnas no deseadas si existen
            columnas_presentes = [col for col in comportamientos_a_eliminar if col in df.columns]
            df = df.drop(columns=columnas_presentes)

            # Guardar el archivo sobrescribiéndolo
            df.to_csv(file_path, index=False)
