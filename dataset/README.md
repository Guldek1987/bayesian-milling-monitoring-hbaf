# MSM dataset setup

This repository uses only the **MTConnect CSV files, expert `label.csv` files, two MTConnect XML information models, and `dataset_summary.xlsx`** required by the six notebooks. High-frequency audio, video, accelerometer, current-transformer, and NC-program files are not used.

The raw research files are not duplicated in Git history. Instead, `dataset_manifest.csv` records the exact expected subset and SHA-256 hashes, and `download_msm_subset.py` retrieves the public Kaggle dataset and materializes only those files under `dataset/raw/`.

## Source

- Dataset DOI: https://doi.org/10.34740/kaggle/ds/8392825
- Data descriptor: https://doi.org/10.1038/s41597-026-07255-7
- Kaggle slug: `manufuturetoday/multi-sensor-for-metal-milling-anomaly`

## Setup

From the repository root:

```bash
python dataset/download_msm_subset.py
```

The script downloads the public dataset via `kagglehub`, locates every file listed in `dataset_manifest.csv`, copies only those files into `dataset/raw/`, and verifies each SHA-256 checksum. After the final `PASS`, run the notebooks in numerical order (`01` → `06`).

If Kaggle requires authentication in your environment, follow the standard Kaggle API/kagglehub authentication procedure and rerun the command.
