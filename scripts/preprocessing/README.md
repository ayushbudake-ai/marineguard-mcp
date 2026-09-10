# 📊 Dataset & Preprocessing Pipeline Scripts

This folder contains the data conversion, augmentation, and validation scripts for the MarineGuard 50-class unified taxonomy.

## Scripts

- **`convert_fls.py`**: Ingests Forward-Looking Sonar (FLS) datasets and converts annotations to YOLO format.
- **`convert_uatd.py`**: Ingests Underwater Acoustic Target Detection (UATD) dataset annotations.
- **`convert_seaclear.py`**: Converts SeaClear optical and acoustic bounding boxes.
- **`convert_trashcan.py`**: Converts TrashCan dataset instances.
- **`create_combined_dataset.py`**: Combines all normalized subsets into the unified MarineGuard V1 dataset.
- **`validate_marineguard.py`**: Audits bounding box coordinates, class IDs (0-49), and label-image pairings.
- **`create_seaclear_hardlinks.py` / `create_uatd_hardlinks.py`**: Fast local dataset link generators.
