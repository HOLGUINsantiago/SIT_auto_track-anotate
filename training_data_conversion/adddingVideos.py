import os
import subprocess
from deepethogram import projects
import re
import shlex
import pandas as pd
import csv

def nettoyer_csv(filepath):
    lignes_nettoyees = []
    entete_trouvee = False

    with open(filepath, 'r', encoding='utf-8') as f:
        lecteur = csv.reader(f, delimiter=",")
        for ligne in lecteur:
            if not entete_trouvee:
                # Cherche la ligne d'en-tête qui commence par "Time"
                if ligne and ligne[0].strip().lower() == 'time':
                    lignes_nettoyees.append(ligne)
                    entete_trouvee = True
                continue

            # Si on est déjà dans les données, on arrête si la ligne est vide
            if not ligne or all(cell.strip() == "" for cell in ligne):
                break

            lignes_nettoyees.append(ligne)
    return lignes_nettoyees

def extraire_start_end_from_csv(csv_path):
    lignes = nettoyer_csv(csv_path)
    start_time = end_time = None
    for ligne in lignes:
        if len(ligne) < 1:
            continue
        contenu = " ".join(cell.lower() for cell in ligne if cell)
        if "start test" in contenu:
            start_time = float(ligne[0])
        elif "end test" in contenu:
            end_time = float(ligne[0])
    return start_time, end_time

def repair_video_with_ffmpeg(video_path, output_dir, start_time=None, end_time=None):
    filename = os.path.basename(video_path)
    name_no_ext = os.path.splitext(filename)[0]
    safe_name = name_no_ext.replace(" ", "")
    repaired_filename = f"{safe_name}.mp4"
    repaired_path = os.path.join(output_dir, repaired_filename)

    if os.path.exists(repaired_path):
        print(f"[✓] Already repaired: {repaired_filename}")
        return repaired_path

    print(f"[⚙] Repairing: {filename}")
    try:
        # Opciones de corte
        if start_time is not None:
            start_time = float(start_time) - 1140
            if start_time < 0:
                print("[✗] Warning: start_time adjusted to 0 to avoid negative.")
                start_time = None

        ss_part = f"-ss {start_time}" if start_time is not None else ""
        t_part = ""
        if start_time is not None and end_time is not None:
            duration = float(end_time) - 1140 - float(start_time)
            if duration <= 0:
                print("[✗] Error: end_time must be greater than start_time.")
                return None
            t_part = f"-t {duration}"

        cmd = f"""ffmpeg -y {ss_part} -err_detect ignore_err -i "{video_path}" {t_part} \
        -vf "fps=30" -c:v libx264 -preset veryfast -crf 24 \
        -c:a aac -strict experimental "{repaired_path}" """

        subprocess.run(shlex.split(cmd), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return repaired_path
    except subprocess.CalledProcessError as e:
        print(f"[✗] Error repairing {filename}: {e}")
        return None

def ajouter_tous_videos_au_projet(project_config_path, root_video_dir, mode='copy', extensions=None, csv_filter_path=None, time_files=None):
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']

    # Cargar proyecto
    project = projects.load_config(project_config_path)
    execution_dir = os.getcwd()

    # Cargar CSV con nombres de videos si se proporciona
    allowed_video_names = None
    if csv_filter_path is not None and os.path.exists(csv_filter_path):
        df_filter = pd.read_csv(csv_filter_path)
        allowed_video_names = set(os.path.splitext(v)[0] for v in df_filter['video_name'].values)
        print(f"[🔎] Usando filtro de CSV con {len(allowed_video_names)} nombres.")

    videos_paths = []
    for root, dirs, files in os.walk(root_video_dir):
        for file in files:
            name_no_ext = os.path.splitext(file)[0]
            if os.path.splitext(file)[1].lower() in extensions:
                if allowed_video_names is None or name_no_ext in allowed_video_names:
                    full_path = os.path.join(root, file)
                    videos_paths.append(full_path)

    print(f"🔍 Found {len(videos_paths)} video(s) to check and add.")
    
    cont = 0
    for video_path in videos_paths:
        video_name = os.path.splitext(os.path.basename(video_path))[0].replace(" ", "")
        start_time = end_time = None

        # Buscar CSV de tiempo correspondiente
        if time_files:
            csv_path = os.path.join(time_files, f"{video_name}.csv")
            if os.path.exists(csv_path):
                start_time, end_time = extraire_start_end_from_csv(csv_path)
                print(f"[⏱] {video_name}: start={start_time}, end={end_time}")
            else:
                print(f"[!] CSV de tiempo no encontrado para {video_name}")

        repaired_path = repair_video_with_ffmpeg(video_path, output_dir=execution_dir, start_time=start_time, end_time=end_time)
        if repaired_path:
            cont += 1
            try:
                new_path = projects.add_video_to_project(project, repaired_path, mode=mode)
                print(f"[+] Added: {repaired_path} → {new_path} . {cont} / {len(videos_paths)}")
                os.remove(repaired_path)
                print(f"[🗑] Deleted temporary file: {repaired_path}")
            except Exception as e:
                print(f"[✗] Error adding to project {repaired_path}: {e}")
                os.remove(repaired_path)
                print(f"[🗑] Deleted temporary file: {repaired_path}")
        else:
            print(f"[!] Skipped: {video_path} (repair failed)")

# === CONFIGURACIÓN ===
config_path = r"D:\SIT_auto\SIT_deepethogram\project_config.yaml"
videos_dir = r"D:\SIT_auto\corrected_videos"
csv_files_time=r"D:\SIT_auto\adut"
ajouter_tous_videos_au_projet(config_path, videos_dir, mode='copy', time_files = csv_files_time)
