import os
import h5py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, f1_score, accuracy_score

# Paths
deepethogram_root = r"D:\LBN\Maternal_auto_classification_TS7_deepethogram\DATA"
manual_root = r"D:\LBN\Maternal_auto_classification_manualVal_deepethogram\DATA"

# Salida
os.makedirs("comparison_outputs", exist_ok=True)

# Inicialización de métricas
data_records = []

# Procesar cada carpeta de video
for video_dir in os.listdir(deepethogram_root):
    deepe_video_path = os.path.join(deepethogram_root, video_dir)
    manual_video_path = os.path.join(manual_root, video_dir)

    if not os.path.isdir(deepe_video_path) or not os.path.isdir(manual_video_path):
        continue

    # Buscar h5 y csv
    h5_file = os.path.join(deepe_video_path, f"{video_dir}_outputs.h5")
    csv_file = None
    for f in os.listdir(manual_video_path):
        if f.endswith("_labels.csv"):
            csv_file = os.path.join(manual_video_path, f)
            break

    if not os.path.exists(h5_file) or csv_file is None:
        print(f"⚠️ Falta archivo en {video_dir}")
        continue

    print(f"🔍 Procesando {video_dir}")

    # Cargar anotaciones manuales
    labels_df = pd.read_csv(csv_file)
    labels_df = labels_df.drop(columns=['background'], errors='ignore')
    behaviors_manual = labels_df.columns[1:]  # omitir frame si existe
    manual_array = labels_df[behaviors_manual].values

    # Cargar predicciones DeepEthogram
    with h5py.File(h5_file, 'r') as f:
        probs = f['resnet18']['P'][:, 1:]  # quitamos fondo
        thresholds = f['resnet18']['thresholds'][1:]
        class_names = [c.decode('utf-8') for c in f['resnet18']['class_names'][1:]]

    # Filtrar comportamientos comunes
    common_behaviors = [b for b in behaviors_manual if b in class_names]
    model_indices = [class_names.index(b) for b in common_behaviors]
    model_preds = (probs[:, model_indices] >= thresholds[model_indices]).astype(int)

    n_frames = min(manual_array.shape[0], model_preds.shape[0])
    manual_array = manual_array[:n_frames, [list(behaviors_manual).index(b) for b in common_behaviors]]
    model_preds = model_preds[:n_frames, :]

    condition = 'LBN' if 'LBN' in video_dir else 'CONT'

    for i, behavior in enumerate(common_behaviors):
        y_true = manual_array[:, i]
        y_pred = model_preds[:, i]

        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        acc = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        data_records.append({
            "video": video_dir,
            "condition": condition,
            "behavior": behavior,
            "frames_manual_positive": int(np.sum(y_true)),
            "frames_model_positive": int(np.sum(y_pred)),
            "frames_true_positive": int(cm[1, 1]),
            "frames_false_positive": int(cm[0, 1]),
            "frames_false_negative": int(cm[1, 0]),
            "frames_true_negative": int(cm[0, 0]),
            "accuracy": acc,
            "f1_score": f1
        })

# Construir DataFrame general
summary_df = pd.DataFrame(data_records)
summary_df.to_csv("comparison_outputs/per_video_f1_accuracy.csv", index=False)

# ---------- FIGURAS GENERALES Y POR CONDICIÓN ----------

for level, group_df in [('global', summary_df), *list(summary_df.groupby('condition'))]:
    cm_total = np.zeros((2, 2))
    metrics_records = []

    for behavior in group_df['behavior'].unique():
        df_b = group_df[group_df['behavior'] == behavior]
        tp = df_b['frames_true_positive'].sum()
        fp = df_b['frames_false_positive'].sum()
        fn = df_b['frames_false_negative'].sum()
        tn = df_b['frames_true_negative'].sum()

        cm = np.array([[tn, fp], [fn, tp]])
        cm_total += cm

        acc = (tp + tn) / cm.sum()
        f1 = (2 * tp) / (2 * tp + fp + fn) if (2 * tp + fp + fn) != 0 else 0

        metrics_records.append({
            "level": level if isinstance(level, str) else level[0],
            "behavior": behavior,
            "accuracy": acc,
            "f1_score": f1,
            "TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn)
        })

    # Guardar figura matriz de confusión
    disp = ConfusionMatrixDisplay(confusion_matrix=cm_total.astype(int), display_labels=["No", "Yes"])
    disp.plot(cmap="Blues", values_format='d')
    plt.title(f"{level if isinstance(level, str) else level[0]} - Confusion Matrix (Frames)")
    plt.savefig(f"comparison_outputs/{level if isinstance(level, str) else level[0]}_confusion_matrix_frames.png", dpi=300)
    plt.close()

    # Normalizada
    row_sums = cm_total.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    cm_norm = cm_total / row_sums
    sns.heatmap(cm_norm, annot=True, cmap="Blues", xticklabels=["No", "Yes"], yticklabels=["No", "Yes"], fmt=".2f")
    plt.title(f"{level if isinstance(level, str) else level[0]} - Confusion Matrix Normalized")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.savefig(f"comparison_outputs/{level if isinstance(level, str) else level[0]}_confusion_matrix_normalized.png", dpi=300)
    plt.close()

    # Guardar CSV de métricas resumidas por comportamiento
    metrics_df = pd.DataFrame(metrics_records)
    metrics_df.to_csv(f"comparison_outputs/{level if isinstance(level, str) else level[0]}_summary_metrics.csv", index=False)

# FIGURAS DE BARRAS GLOBALES

# Boxplot + puntos para F1-score (cada punto es un video, boxplot del mean)
plt.figure(figsize=(12, 6))
# Calcular el mean F1 por video, comportamiento y condición
mean_f1 = summary_df.groupby(['behavior', 'condition', 'video'])['f1_score'].mean().reset_index()
sns.boxplot(data=mean_f1, x="behavior", y="f1_score", hue="condition", showmeans=True,
            meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black"},
            boxprops=dict(alpha=.5))
sns.stripplot(data=mean_f1, x="behavior", y="f1_score", hue="condition", dodge=True, alpha=0.7, linewidth=0.5, marker=".", color="black")
plt.title("F1 Score por comportamiento y condición (boxplot=mean, puntos=videos)")
plt.xticks(rotation=45)
plt.tight_layout()
handles, labels = plt.gca().get_legend_handles_labels()
n = len(set(mean_f1['condition']))
plt.legend(handles[:n], labels[:n], title="Condición")
plt.savefig("comparison_outputs/F1_scores_by_behavior_condition_boxplot.png", dpi=300)
plt.close()

plt.figure(figsize=(10, 5))
sns.barplot(data=summary_df, x="behavior", y="accuracy", hue="condition")
plt.title("Accuracy por comportamiento y condición")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("comparison_outputs/Accuracy_by_behavior_condition.png", dpi=300)
plt.close()

# Guardar lista de videos con peor F1 promedio
worst_f1_videos = (
    summary_df.groupby("video")["f1_score"]
    .mean()
    .sort_values()
    .reset_index()
    .rename(columns={"f1_score": "mean_f1_score"})
)
worst_f1_videos.to_csv("comparison_outputs/videos_worst_f1.csv", index=False)

print("✅ Comparación completada: figuras y CSV exportados sin generar imágenes por video, con resumen global y por condición.")
print("📉 Lista de videos con peor F1-score guardada en 'comparison_outputs/videos_worst_f1.csv'")