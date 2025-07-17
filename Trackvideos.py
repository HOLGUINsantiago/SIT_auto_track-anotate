import os
from pathlib import Path
import subprocess
import sys

# === Configuración de variables ===
MODEL_centroid_PATH = r"D:\SIT_auto\SLEAP_track\models\250702_114533.centroid.n=765"
MODEL_centered_instance_PATH = r"D:\SIT_auto\SLEAP_track\models\250702_132640.centered_instance.n=765"

VIDEOS_FOLDER = Path(r"D:\SIT_auto\for_tracking_ado")
OUTPUT_FOLDER = r"D:\SIT_auto\tracked_videos"
MAX_INSTANCES = 2
MAX_TRACKS = 2

# Crear carpeta de salida si no existe
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

# === Procesar cada video individualmente ===
for video_file in VIDEOS_FOLDER.glob("*.mp4"):
    print(f"\nProcesando: {video_file.name}")

    command = (
        f'sleap-track '
        f'-m "{MODEL_centroid_PATH}" '
        f'-m "{MODEL_centered_instance_PATH}" '
        f'--tracking.tracker flowmaxtracks '
        f'--tracking.similarity centroid '
        f'--tracking.match hungarian '
        f'--tracking.max_tracking 1 '
        f'--tracking.max_tracks {MAX_TRACKS} '
        f'-n {MAX_INSTANCES} '
        f'-o "{OUTPUT_FOLDER}\{video_file.stem}" '
        f'"{video_file}"'
    )

    print("Comando a ejecutar:")
    print(command)

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    print(result.stdout)
    print(result.stderr)
