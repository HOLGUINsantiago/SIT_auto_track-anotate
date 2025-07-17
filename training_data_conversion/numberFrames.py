from deepethogram.file_io import VideoReader
from pathlib import Path
import csv

# Ruta raíz del dataset
root_path = Path(r'D:\LBN\Maternal_auto_classification_train_deepethogram\DATA')

# Preparamos el archivo CSV de salida
output_csv = r'D:\SIT_auto\training_data_conversion\frames_per_video.csv'

# Abrimos el CSV para escritura
with open(output_csv, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['video', 'frames'])

    # Recorremos todas las carpetas dentro de DATA
    for video_file in root_path.glob('**/*.mp4'):
        try:
            # Abrimos el video con VideoReader
            reader = VideoReader(str(video_file))
            # Calculamos el número de frames
            num_frames = len(reader) - 1
            # Escribimos en el CSV: nombre de archivo (sin ruta completa) y frames
            writer.writerow([video_file.name, num_frames])
            print(f'{video_file.name} -> {num_frames} frames')
        except Exception as e:
            print(f'Error processing {video_file}: {e}')
