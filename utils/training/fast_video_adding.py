import os
import subprocess
from deepethogram import projects
import re

def repair_video_with_ffmpeg(video_path, output_dir):
    import shlex

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
        cmd = f"""ffmpeg -y -err_detect ignore_err -i "{video_path}" \
        -vf "fps=30" -c:v libx264 -preset veryfast -crf 24 \
        -c:a aac -strict experimental "{repaired_path}" """
        
        subprocess.run(shlex.split(cmd), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return repaired_path
    except subprocess.CalledProcessError as e:
        print(f"[✗] Error repairing {filename}: {e}")
        return None


def ajouter_tous_videos_au_projet(project_config_path, root_video_dir, mode='copy', extensions=None):
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']

    project = projects.load_config(project_config_path)
    execution_dir = os.getcwd()

    videos_paths = []
    pattern = re.compile(r".*_(\d{2})-(\d{2})-(\d{2})") 
    for root, dirs, files in os.walk(root_video_dir):
        for file in files:
            match = pattern.match(file)
            if match:
                hour = int(match.group(1))
                if 8 > hour or hour >= 20:
                    if os.path.splitext(file)[1].lower() in extensions:
                        full_path = os.path.join(root, file)
                        videos_paths.append(full_path)

    print(f"Found {len(videos_paths)} videos to check and add.")
    cont = 0
    for video_path in videos_paths:
        video_name = os.path.basename(video_path)

        repaired_path = repair_video_with_ffmpeg(video_path, output_dir=execution_dir)
        if repaired_path:
            cont += 1
            try:
                new_path = projects.add_video_to_project(project, repaired_path, mode=mode)
                print(f"[+] Added: {repaired_path} → {new_path} . {cont} / {len(videos_paths)}")
                os.remove(repaired_path)
                print(f"[🗑] Deleted temporary file: {repaired_path}")
            except Exception as e:
                print(f"[✗] Error adding to project {repaired_path}: {e}")
        else:
            print(f"[!] Skipped: {video_path} (repair failed)")

# === CONFIGURACIÓN ===
config_path = r"D:\LBN\Maternal_auto_classification_deepethogram\project_config.yaml"
videos_dir = r"Z:\Marion\2. Tests - Manuels - Data\3. LBN\3. Rawdata\1. VEAVE_LBN-CONT\Cohorte 3 -Dec2024\Cage 7 - LBN"

ajouter_tous_videos_au_projet(config_path, videos_dir, mode='copy')