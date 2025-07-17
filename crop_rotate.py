import os
from pathlib import Path
import subprocess

def preprocess_videos(
    input_folder,
    output_folder,
    skip_minutes=0,
    rotate=False,
    rotate_angle=90,
    crop=None  # crop = (w, h, x, y)
):
    """
    Procesa todos los videos de una carpeta:
    - Salta los primeros minutos.
    - Rota si se indica.
    - Recorta si se indica.
    - Exporta como .mp4 optimizado para tracking.

    Args:
        input_folder (str or Path): Carpeta de entrada.
        output_folder (str or Path): Carpeta de salida.
        skip_minutes (int): Minutos a saltar al inicio.
        rotate (bool): Si se rota o no.
        rotate_angle (int): 90 o 270.
        crop (tuple): (w, h, x, y) para cropping tras rotación.
    """

    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)

    video_files = list(input_folder.glob("*.*"))

    for video_file in video_files:
        if video_file.suffix.lower() == ".mp4":
            continue

        out_path = output_folder / f"{video_file.stem}.mp4"

        # ffprobe para obtener dimensiones
        probe = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            str(video_file)
        ], capture_output=True, text=True)

        if probe.returncode != 0:
            print(f"❌ No se pudo analizar {video_file.name}. Skipping.")
            continue

        w, h = map(int, probe.stdout.strip().split('x'))

        # Generar filtro
        filters = []

        if rotate:
            if rotate_angle == 90:
                filters.append("transpose=1")  # clockwise
            elif rotate_angle == 270:
                filters.append("transpose=2")  # counter-clockwise
            else:
                print(f"⚠️ Ángulo de rotación {rotate_angle} no soportado, omitiendo rotación.")

        if crop:
            crop_w, crop_h, crop_x, crop_y = crop
            filters.append(f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}")

        filter_str = ",".join(filters) if filters else "null"

        cmd = [
            "ffmpeg",
            "-ss", str(skip_minutes * 60),
            "-i", str(video_file),
            "-vf", filter_str,
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "fast",
            "-c:a", "copy",
            str(out_path)
        ]

        print(f"▶️ Procesando {video_file.name}...")
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print(f"✅ {out_path.name} creado correctamente.")
        else:
            print(f"❌ Error al procesar {video_file.name}.")

    print("✅ Procesamiento de todos los videos completado.")

# ==== EJEMPLO DE USO CON TUS PARÁMETROS ORIGINALES ====

if __name__ == "__main__":
    input_folder = r"Z:\Marion\2. Tests - Manuels - Data\6. SIT\3. Rawdata\1. VEAVE_LBN-CONT\Cohorte 3\Ado"
    output_folder = "for_tracking_ado"

    preprocess_videos(
        input_folder=input_folder,
        output_folder=output_folder,
        skip_minutes=19,                     # ⏩ saltar 19 min
        rotate=False,                         # ✅ rotar
    )
