## DeepEthogram Annotation Preparation Pipeline

This pipeline prepares and merges manual annotations to train DeepEthogram on behavioral videos. It includes:

- Cleaning and aligning CSV manual annotations with frame counts.
- Shifting annotations for alignment.
- Merging annotations from different raters (e.g., JS and LL).
- Repairing or trimming videos to match annotation windows.

## 1 Use Case: A single annotation file exist for each video

### 1. Add your videos to DeG 

Your solomon CSVs are expected to have a column Test where "start test" and "end test" are specified

```python
config_path = r"SIT_deepethogram\project_config.yaml"
videos_dir = r"corrected_videos"
csv_files_time=r"PATH_TO_SOLOMON_FILES"
ajouter_tous_videos_au_projet(config_path, videos_dir, mode='copy', time_files = csv_files_time)
```
Copy and paste this at the end of the [adding videos script](..\training_data_conversion\1_adddingVideos.py) replacing the current code present on the script at the end

### 2. Create DeG compatible binary csv files :

Use the [transformation script](..\training_data_conversion\2_transformSolomonCompatibleDeG.py)

```python
traiter_lot(
    dossier_csvs=r"PATH_TO_SOLOMON_FILES",
    dossier_videos=r"SIT_deepethogram\DATA",
    dossier_sortie="./videos_annotations/",
    shift_fraction=0.003,
    delimiter_csv=",",        
    decimal_csv="."           
)
```

Modify the `traiter_lot` function call with this new arguments and Run the script on your deg_social env (`conda activate deg_social` or selecting the environment on left corner before running)

## 2 Use Case: Two annotation files (two annotators) exist for each video

### 1. Add your videos to DeG

Your Solomon CSVs for **each annotator (e.g., JS and LL)** should have a `Test` column with "start test" and "end test" specified.

```python
config_path = r"SIT_deepethogram\project_config.yaml"
videos_dir = r"corrected_videos"
csv_files_time = r"PATH_TO_SOLOMON_FILES"

ajouter_tous_videos_au_projet(config_path, videos_dir, mode='copy', time_files=csv_files_time)
```
Copy and paste this at the end of the [adding videos script](..\training_data_conversion\1_adddingVideos.py) replacing the current code present on the script at the end

### 2. Create DeG compatible binary csv files :

Use the [transformation script](..\training_data_conversion\2_transformSolomonCompatibleDeG.py), one for each annotator (output on two different folders)

```python
traiter_lot(
    dossier_csvs=r"PATH_TO_JS_SOLOMON_FILES",
    dossier_videos=r"SIT_deepethogram\DATA",
    dossier_sortie="./ANNOTATOR1_videos_annotations/",
    shift_fraction=0.003,
    delimiter_csv=",",
    decimal_csv="."
)

traiter_lot(
    dossier_csvs=r"PATH_TO_LL_SOLOMON_FILES",
    dossier_videos=r"SIT_deepethogram\DATA",
    dossier_sortie="./ANNOTATOR2_videos_annotations/",
    shift_fraction=0.003,
    delimiter_csv=",",
    decimal_csv="."
)
```

### Merge both annotation files
Use the [merging script](..\training_data_conversion\3_mergeCSV.py) to combine the cleaned binary CSVs from BOTH annotators:

```python
fusionar_carpetas(
    "ANNOTATOR1_videos_annotations",
    "ANNOTATOR2_videos_annotations",
    "merged_videos_annotations"
)
```

This will create a single merged annotation file per video using a logical OR operation across both annotators' labels, resulting in robust, DeG-compatible CSV files for training.

**Summary Workflow**
1. Add videos to DeG using ajouter_tous_videos_au_projet.

2. Create cleaned CSV annotations for each annotator using traiter_lot.

3. Merge annotations using fusionar_carpetas.

4. Use merged_videos_annotations in your DeG project for training or active learning.

By following this workflow, you ensure consistent, clean, and merged annotations across your annotators for DeepEthogram projects while respecting precise experimental windows defined by your start test and end test markers.