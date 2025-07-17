import os
import pandas as pd

def chercher_fichiers_comportement(dossier,
                                    pattern_fin='_outputs_labels_predictions.csv',
                                    comportements_recherches=None,
                                    output_csv=None,
                                    mot_clef_fichier=None):
    if comportements_recherches is None:
        comportements_recherches = []

    video_names = []

    for racine, _, fichiers in os.walk(dossier):
        for fichier in fichiers:
            if not fichier.endswith(pattern_fin):
                continue
            if mot_clef_fichier and mot_clef_fichier not in fichier:
                continue

            chemin_complet = os.path.join(racine, fichier)

            try:
                df = pd.read_csv(chemin_complet)
                colonnes_valides = [c for c in comportements_recherches if c in df.columns]

                if not colonnes_valides:
                    continue

                if (df[colonnes_valides] == 1).any().all():
                    video_name = fichier.replace(pattern_fin, "")
                    video_names.append(video_name)

            except Exception as e:
                print(f"Erreur lors du traitement de {chemin_complet} : {e}")

    if output_csv:
        pd.DataFrame({'video_name': video_names}).to_csv(output_csv, index=False)
        print(f"[💾] Résultats enregistrés dans : {output_csv}")

    return video_names


if __name__ == "__main__":
    dossier = r"D:\LBN\Maternal_auto_classification_train_deepethogram\DATA"
    comportements = ["Carryingpups"]
    mot_clef = ""
    output_csv_path = f"D:\\LBN\\videos_with_{comportements[0]}_{mot_clef}.csv"

    resultats = chercher_fichiers_comportement(
        dossier,
        pattern_fin='.csv',
        comportements_recherches=comportements,
        output_csv=output_csv_path,
        mot_clef_fichier=None
    )

    print("\nVidéos contenant les comportements recherchés :")
    for name in resultats:
        print(f"- {name}")
