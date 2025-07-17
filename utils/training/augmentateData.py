import cv2
import numpy as np
import os

# ------- Augmentations -------
def flip_horizontal(frame):
    return cv2.flip(frame, 1)

def adjust_brightness_contrast(frame, brightness=30, contrast=30):
    return cv2.convertScaleAbs(frame, alpha=1 + contrast / 100, beta=brightness)

def zoom_crop(frame, zoom_factor=1.1):
    h, w = frame.shape[:2]
    nh, nw = int(h / zoom_factor), int(w / zoom_factor)
    y1, x1 = (h - nh) // 2, (w - nw) // 2
    cropped = frame[y1:y1+nh, x1:x1+nw]
    return cv2.resize(cropped, (w, h))

def blur(frame):
    return cv2.GaussianBlur(frame, (5, 5), 0)

# ------- Write video -------
def process_and_save(video_path, output_name, transform_fn):
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    out = cv2.VideoWriter(output_name, fourcc, fps, (width, height))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        transformed = transform_fn(frame)
        out.write(transformed)
    
    cap.release()
    out.release()
    print(f"Saved: {output_name}")

# ------- Combinations -------
def combo123(frame):
    return blur(zoom_crop(adjust_brightness_contrast(frame)))

def combo234(frame):
    return flip_horizontal(blur(zoom_crop(frame)))

def combo124(frame):
    return blur(adjust_brightness_contrast(flip_horizontal(frame)))

# ------- Main -------
def generate_augmented_videos(video_path):
    base = os.path.splitext(os.path.basename(video_path))[0]
    process_and_save(video_path, f'{base}_flip.mp4', flip_horizontal)
    process_and_save(video_path, f'{base}_bright_contrast.mp4', adjust_brightness_contrast)
    process_and_save(video_path, f'{base}_zoom_crop.mp4', zoom_crop)
    process_and_save(video_path, f'{base}_blur.mp4', blur)
    
    # Combinations de 3
    process_and_save(video_path, f'{base}_combo123.mp4', combo123)
    process_and_save(video_path, f'{base}_combo234.mp4', combo234)
    process_and_save(video_path, f'{base}_combo124.mp4', combo124)

# ------- Run -------
if __name__ == '__main__':
    base_path = r'Maternal_auto_classification_train_deepethogram/DATA'

    video_names = [
        "Cage2-LBN-2024-12-11_20-42-14",
        "Cage2-LBN-2024-12-11_21-02-14",
        "Cage2-LBN-2024-12-11_22-52-14",
        "Cage3-LBN-2024-12-08_21-38-35",
        "Cage3-LBN-2024-12-08_22-28-35",
        "Cage3-LBN-2024-12-10_20-08-42",
        "Cage3-LBN-2024-12-10_21-28-42",
        "Cage3-LBN-2024-12-11_04-38-42",
        "Cage3-LBN-2024-12-12_04-12-15",
        "Cage3-LBN-2024-12-12_04-52-15",
        "Cage3-LBN-2024-12-14_06-23-41",
        "CageA-LBN-2024-07-06_05-33-20"
    ]

    for name in video_names:
        clean_name = name.strip()  # elimina espacios extra
        video_file = os.path.join(base_path, clean_name, f"{clean_name}.mp4")
        if os.path.exists(video_file):
            generate_augmented_videos(video_file)
        else:
            print(f"❌ Archivo no encontrado: {video_file}")

            