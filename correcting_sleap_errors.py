import sys
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
import sleap
import os
import glob
import colorsys
from PyQt5.QtCore import QElapsedTimer

class SleapTrackingCorrector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SLEAP Tracking Corrector")
        self.resize(1400, 900)  # Bigger initial window

        self.elapsed_accumulated = 0
        self.elapsed_timer = QElapsedTimer()
        self.playback_start_time = 0
        self.paused_time_accum = 0

        # ==== MAIN LAYOUT ====
        main_layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(main_layout)

        # ==== LEFT: VIDEO DISPLAY ====
        video_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(video_layout, stretch=4)

        self.label = QtWidgets.QLabel("Load a video to start.")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setMinimumSize(1000, 700)  # Bigger video
        video_layout.addWidget(self.label)

        self.frame_counter_label = QtWidgets.QLabel("Frame: 0")
        self.frame_counter_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        video_layout.addWidget(self.frame_counter_label)

        # ==== BOTTOM: BIG PAUSE + INVERT ====
        bottom_layout = QtWidgets.QHBoxLayout()
        video_layout.addLayout(bottom_layout)

        self.pause_button = QtWidgets.QPushButton("⏸️ Pause / ▶️ Resume")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setStyleSheet("font-size: 22px; padding: 15px; background-color: #007BFF; color: white; border-radius: 10px;")
        bottom_layout.addWidget(self.pause_button)

        self.invert_button = QtWidgets.QPushButton("🔄 Invert Identities")
        self.invert_button.clicked.connect(self.ask_and_invert_identities)
        self.invert_button.setStyleSheet("font-size: 22px; padding: 15px; background-color: #28A745; color: white; border-radius: 10px;")
        bottom_layout.addWidget(self.invert_button)

        # ==== RIGHT: SETTINGS & ACTIONS ====
        side_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(side_layout, stretch=1)

        # Speed selector
        speed_label = QtWidgets.QLabel("Playback FPS:")
        speed_label.setStyleSheet("font-size: 18px;")
        side_layout.addWidget(speed_label)

        self.speed_selector = QtWidgets.QComboBox()
        self.speed_selector.addItems(["30", "45", "60", "120"])
        self.speed_selector.setStyleSheet("font-size: 18px; padding: 10px;")
        side_layout.addWidget(self.speed_selector)

        # Load button
        self.load_button = QtWidgets.QPushButton("📂 Load Video & Predictions")
        self.load_button.clicked.connect(self.load_files)
        self.load_button.setStyleSheet("font-size: 18px; padding: 12px; background-color: #17A2B8; color: white; border-radius: 8px;")
        side_layout.addWidget(self.load_button)

        # Save button
        self.save_button = QtWidgets.QPushButton("💾 Save Corrected Predictions")
        self.save_button.clicked.connect(self.save_predictions)
        self.save_button.setStyleSheet("font-size: 18px; padding: 12px; background-color: #FFC107; color: black; border-radius: 8px;")
        side_layout.addWidget(self.save_button)

        # Export button
        self.export_back_btn = QtWidgets.QPushButton("🎥 Export Video with 'back'")
        self.export_back_btn.clicked.connect(self.export_video_with_back)
        self.export_back_btn.setStyleSheet("font-size: 18px; padding: 12px; background-color: #6F42C1; color: white; border-radius: 8px;")
        side_layout.addWidget(self.export_back_btn)

        side_layout.addStretch()

        # ==== Timer ====
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.sync_next_frame)
        self.elapsed_timer = QtCore.QElapsedTimer()

        # Variables
        self.labels = None
        self.filtered_frames = []
        self.frame_idx = 0
        self.track_swapped = False
        self.paused = False
        self.colors = []
        self.video = None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_P:
            self.toggle_pause()
        elif event.key() == QtCore.Qt.Key.Key_I:
            self.ask_and_invert_identities()


    def toggle_pause(self):
        if self.paused:
            # Reanudar: simplemente reiniciar el timer, sin modificar playback_start_time
            self.elapsed_timer.restart()
            self.timer.start(10)
            self.paused = False
            self.pause_button.setText("Pause")
            print(f"[DEBUG] Resumed at frame {self.frame_idx}, playback_start_time={self.playback_start_time}ms")
        else:
            # Pausar: guardar el tiempo transcurrido hasta ahora en playback_start_time
            self.playback_start_time += self.elapsed_timer.elapsed()
            self.timer.stop()
            self.paused = True
            self.pause_button.setText("Resume")
            print(f"[DEBUG] Paused at frame {self.frame_idx}, playback_start_time={self.playback_start_time}ms")

    def load_files(self):
        video_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Video")
        pred_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select SLEAP Predictions Folder")

        if video_path and pred_folder:
            print(f"[DEBUG] Loading video: {video_path}")
            # No abrimos con cv2.VideoCapture, sino guardamos path para buscar en labels.videos
            self.video_path = video_path

            pred_file = self.find_latest_prediction(pred_folder, video_path)
            if pred_file is None:
                QtWidgets.QMessageBox.warning(self, "Warning", "No prediction file found for this video.")
                return

            print(f"[DEBUG] Loaded predictions from: {pred_file}")
            self.labels = sleap.load_file(pred_file)
            self.filtered_frames = self.get_labels_for_video(self.labels, video_path)
            print(f"[DEBUG] Loaded {len(self.filtered_frames)} frames with labels for this video.")
            self.frame_idx = 0
            self.assign_colors()

            # *** Obtenemos el backend de video SLEAP para el video cargado ***
            # SLEAP puede tener varios videos, buscamos el que coincide con el video_path
            self.video = None
            for v in self.labels.videos:
                if os.path.basename(v.filename) == os.path.basename(video_path):
                    self.video = v
                    break
            if self.video is None:
                QtWidgets.QMessageBox.warning(self, "Warning", "No matching video backend found in predictions.")
                return

            # Video info
            self.video_frame_count = self.video.num_frames
            self.video_fps = self.video.fps if hasattr(self.video, "fps") else 30  # fallback

            self.start_playback()

    def find_latest_prediction(self, pred_folder, video_path):
        video_basename = os.path.splitext(os.path.basename(video_path))[0].lower()
        prediction_files = glob.glob(os.path.join(pred_folder, "*.slp")) + glob.glob(os.path.join(pred_folder, "*.h5"))
        matching_files = []
        for f in prediction_files:
            try:
                labels = sleap.load_file(f)
                video_filenames = [os.path.splitext(os.path.basename(v.filename))[0].lower() for v in labels.videos]
                if video_basename in video_filenames:
                    matching_files.append(f)
            except Exception as e:
                print(f"Error loading {f}: {e}")

        if not matching_files:
            return None
        print(matching_files)
        latest_file = max(matching_files, key=os.path.getmtime)
        return latest_file

    def get_labels_for_video(self, labels, video_path):
        video_basename = os.path.basename(video_path).lower()
        return [
            frame for frame in labels.labeled_frames
            if hasattr(frame.video, "filename") and os.path.basename(frame.video.filename).lower() == video_basename
        ]

    def assign_colors(self):
        # HSV colormap → RGB para cada instancia
        n_instances = max((len(frame.instances) for frame in self.filtered_frames), default=1)
        self.colors = []
        for i in range(n_instances):
            hue = i / n_instances
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            rgb = tuple(int(255 * c) for c in rgb)
            self.colors.append(rgb)

    def start_playback(self):
        fps = int(self.speed_selector.currentText())
        self.fps = fps
        self.mspf = 1000 / fps
        self.elapsed_timer.restart()
        self.playback_start_time = 0
        self.timer.start(10)
        self.pause_button.setText("Pause")
        self.paused = False
        print(f"[DEBUG] Playback started at {fps} FPS (start_playback)")

    def sync_next_frame(self):
        # Permitir cambio de velocidad en tiempo real
        fps = int(self.speed_selector.currentText())
        if fps != self.fps:
            # Ajustar playback_start_time para que el frame actual no cambie
            elapsed = self.elapsed_timer.elapsed() + self.playback_start_time
            # El frame actual antes del cambio
            current_frame = int((elapsed / 1000) * self.fps)
            # El tiempo base para ese frame con el nuevo fps
            self.playback_start_time = (current_frame / fps) * 1000
            self.fps = fps
            self.mspf = 1000 / fps
            self.elapsed_timer.restart()
            print(f"[DEBUG] FPS changed to {fps}, mspf={self.mspf}, adjusted playback_start_time={self.playback_start_time}")
        if self.paused:
            return  # No actualizar frame_idx si está en pausa
        elapsed = self.elapsed_timer.elapsed() + self.playback_start_time
        expected_frame = int((elapsed / 1000) * self.fps)
        if expected_frame != self.frame_idx:
            self.frame_idx = expected_frame
            self.next_frame()

    def next_frame(self):
        if self.video is None or self.paused:
            return

        elapsed_ms = self.playback_start_time + self.elapsed_timer.elapsed()
        current_frame = int((elapsed_ms / 1000) * self.fps)

        if current_frame >= self.video_frame_count:
            current_frame = 0
            self.playback_start_time = 0
            self.elapsed_timer.restart()
            print(f"[DEBUG] Looping video, restarting playback.")

        self.frame_idx = current_frame

        # Obtener frame sincronizado
        frame = self.video.get_frame(self.frame_idx)  # (H, W, C), RGB
        if frame is None:
            print(f"[DEBUG] Failed to get frame at index {self.frame_idx}")
            return

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Dibujar instancias con colores según track.id
        labeled_frame = None
        for lf in self.filtered_frames:
            if hasattr(lf, "frame_idx") and lf.frame_idx == self.frame_idx:
                labeled_frame = lf
                break

        if labeled_frame is not None:
            instances = labeled_frame.instances
            for inst in instances:
                # Usar track.id como base del color
                track_id = inst.track.name if inst.track is not None else 0
                color = self.instance_color(track_id)  # Usa track_id para color consistente
                for kp in inst.points:
                    if kp is not None and not np.isnan(kp.x) and not np.isnan(kp.y):
                        pos = (int(kp.x), int(kp.y))
                        cv2.circle(frame_bgr, pos, 5, color, -1)

        # Convertir a QImage para mostrar en PyQt
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        qimg = QtGui.QImage(frame_rgb.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap.scaled(self.label.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio))

        self.frame_counter_label.setText(f"Frame: {self.frame_idx + 1}")

    def instance_color(self, track_id: str):
        import colorsys
        import hashlib

        hash_int = int(hashlib.sha256(track_id.encode('utf-8')).hexdigest(), 16)
        hue = (hash_int * 0.618033988749895) % 1

        # Si track_id termina en '0' o '1', fuerza el opuesto para esos dos para probar contraste
        if track_id.endswith('0'):
            hue = hue  # Normal
        elif track_id.endswith('1'):
            hue = (hue + 0.5) % 1  # Color opuesto

        r, g, b = colorsys.hsv_to_rgb(hue, 0.9, 0.95)

        # OpenCV espera BGR, así que devolvemos en orden (b, g, r)
        return int(b * 255), int(g * 255), int(r * 255)


    def ask_and_invert_identities(self):
        if self.filtered_frames and self.frame_idx < len(self.filtered_frames):
            self.invert_identities_from_frame(self.frame_idx)

    def invert_identities_from_frame(self, start_frame_idx):
        """
        Invierte las identidades (tracks y posiciones) de las dos primeras instancias
        desde start_frame_idx (incluido) hasta el final.
        """
        start_frame_idx -= 30
        for idx in range(start_frame_idx, len(self.filtered_frames)):
            frame = self.filtered_frames[idx]
            if len(frame.instances) >= 2:
                # Intercambiar tracks
                frame.instances[0].track, frame.instances[1].track = (
                    frame.instances[1].track,
                    frame.instances[0].track,
                )
                # Intercambiar posiciones 
                frame.instances[0], frame.instances[1] = (
                    frame.instances[1],
                    frame.instances[0],
                )
        print(f"[INFO] Identidades invertidas desde el frame {start_frame_idx}.")

    def save_predictions(self):
        if not self.labels:
            QtWidgets.QMessageBox.warning(self, "Warning", "No predictions loaded.")
            return

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Corrected Predictions", "", "SLEAP Files (*.slp *.h5)")
        if not save_path:
            return

        self.labels.save(save_path)
        QtWidgets.QMessageBox.information(self, "Saved", f"Predictions saved to {save_path}")

    def export_video_with_back(self):
        folder = r"D:\SIT_auto\corrected_videos"

        # Nombre original del archivo
        filename = os.path.basename(self.video_path)  # saca solo el nombre con extensión

        # Si quieres cambiar la extensión a .mp4 o similar (recomendado)
        base_name, ext = os.path.splitext(filename)
        new_filename = base_name + ".mp4"  # o .avi, según códec que uses

        # Ruta completa
        save_path = os.path.join(folder, new_filename)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = None

        progress = QtWidgets.QProgressDialog("Exporting video...", "Cancel", 0, self.video_frame_count, self)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.show()

        for frame_idx in range(self.video_frame_count):
            if progress.wasCanceled():
                break

            frame = self.video.get_frame(frame_idx)
            if frame is None:
                continue
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # 🔹 Usar self.filtered_frames que incluye las inversiones
            labeled_frame = next((lf for lf in self.filtered_frames if lf.frame_idx == frame_idx), None)

            if labeled_frame is not None:
                for inst in labeled_frame.instances:
                    for kp in inst.points:
                        if kp is not None :
                            x, y = int(kp.x), int(kp.y)
                            track_id = inst.track.name if inst.track is not None else 0
                            color = self.instance_color(track_id)
                            cv2.circle(frame_bgr, (x, y), 2, color, -1)

            if out is None:
                height, width, _ = frame_bgr.shape
                out = cv2.VideoWriter(save_path, fourcc, self.fps, (width, height))

            out.write(frame_bgr)
            progress.setValue(frame_idx)

        if out is not None:
            out.release()

        progress.close()
        QtWidgets.QMessageBox.information(self, "Exported", f"Video exported to {save_path}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = SleapTrackingCorrector()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    import cv2  # Solo importamos cv2 para dibujar y convertir color
    main()
