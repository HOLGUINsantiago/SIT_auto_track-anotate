import h5py
import numpy as np
import pandas as pd

def extraire_meilleure_f1(path_h5, mode='last', output_csv=None):
    """
    mode: 'last', 'max_count', 'best_avg'
    """
    class_names = ["background",  "Contactbyhost",  "Contactbyvisitor",  "Followbyhost",  "Followbyvisitor",  "Pawcontrol(host)",  "Rearing",  "Tailrattling",  "Grooming"]
    with h5py.File(path_h5, 'r') as f:
        print("Contenu du fichier :", list(f.keys()))
        split = 'val'
        group = f[split]

        f1 = group['f1_by_class'][:]  # (epochs, classes)
        f1_mean_nobg = group['f1_class_mean_nobg'][:]  # (epochs,)
        nb_epochs = f1.shape[0]

        if mode == 'last':
            best_epoch = nb_epochs - 1
            print("🔚 Mode sélectionné : dernière époque")
        elif mode == 'max_count':
            counts = [(f1[i, 1:] > f1_mean_nobg[i]).sum() for i in range(nb_epochs)]
            best_epoch = int(np.argmax(counts))
            print(f"📊 Mode sélectionné : max_count -> meilleure époque = {best_epoch} (avec {counts[best_epoch]} classes au-dessus de la moyenne)")
        elif mode == 'best_avg':
            best_epoch = int(np.argmax(f1_mean_nobg))
            print(f"📈 Mode sélectionné : best_avg -> meilleure époque = {best_epoch} (F1 moy. nobg = {f1_mean_nobg[best_epoch]:.4f})")
        else:
            raise ValueError("Mode invalide. Utilise 'last', 'max_count' ou 'best_avg'.")

        # Extraire F1 à la meilleure époque
        f1_best = f1[best_epoch]
        print(f"\n--- F1 par comportement (val, époque {best_epoch}) ---")
        for i, name in enumerate(class_names):
            print(f"{name}: F1 = {f1_best[i]:.4f}")

        # Sauvegarde CSV si demandé
        if output_csv:
            df_out = pd.DataFrame({
                'class': class_names,
                'f1_val': f1_best
            })
            df_out.to_csv(output_csv, index=False)
            print(f"\n✅ Résultats enregistrés dans : {output_csv}")

        return best_epoch, f1_best


# Exemple d'utilisation
if __name__ == "__main__":
    model = r"D:\SIT_auto\SIT_deepethogram\models\250715_141521_feature_extractor_train"
    path = model +  r'\classification_metrics.h5'
    mode = 'best_avg' 
    output_csv = r'D:\SIT_auto\val_f1_by_class.csv'

    extraire_meilleure_f1(path, mode=mode, output_csv=output_csv)
