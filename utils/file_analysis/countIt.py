import os
import pandas as pd

# Ruta base
base_dir = r'D:\LBN\Maternal_auto_classification_train_deepethogram\DATA'

# Inicializar contadores por grupo
counts_cont = None
counts_lbn = None

videos_cont = 0
videos_lbn = 0
# Recorrer archivos
for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith('_labels.csv'):
            file_path = os.path.join(root, file)
            df = pd.read_csv(file_path)

            # Quitar primera columna si es un índice sin nombre
            if df.columns[0] == '':
                df = df.iloc[:, 1:]

            # Sumar los valores por columna
            counts = df.sum()

            # Clasificar por tipo
            if 'CONT' in file:
                videos_cont += 1 
                if counts_cont is None:
                    counts_cont = counts
                else:
                    counts_cont += counts
            elif 'LBN' in file:
                videos_lbn += 1
                if counts_lbn is None:
                    counts_lbn = counts
                else:
                    counts_lbn += counts

# Mostrar resultados
print("\nTotal de frames por comportamiento en archivos CONT:")
print(counts_cont.astype(int))

print("\nTotal de frames por comportamiento en archivos LBN:")
print(counts_lbn.astype(int))


print("\nvideos CONT:")
print(videos_cont)

print("\nvideos LBN:")
print(videos_lbn)