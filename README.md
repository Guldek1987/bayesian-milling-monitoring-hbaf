# Bayesian Milling Monitoring with HBAF

**Hierarchical Bayesian Adaptive Fusion (HBAF) for leakage-safe CNC milling process monitoring, uncertainty-aware decision support, and cross-machine generalization analysis.**

This repository contains the reproducible computational pipeline supporting a study of intervention-risk monitoring in CNC milling using the **Multi-Sensor and MTConnect (MSM) dataset**. The project combines experiment-disjoint data preparation, causal prefix representations, strong ML/DL/Bayesian benchmarks, and an adaptive hierarchical Bayesian fusion model.

<p align="center">
  <img src="figures/1_data_preparation_pipeline.png" width="880" alt="Leakage-safe MSM data preparation pipeline">
</p>

## Research objective

The study evaluates whether a Bayesian hybrid decision-support model can remain competitive with strong discriminative alternatives while providing calibrated probabilities, input-dependent expert fusion, and explicit fusion-layer uncertainty under substantial between-experiment and cross-machine distribution shift.

The proposed **HBAF** architecture combines:

- a nonlinear **TabM** expert;
- a probabilistic **Gaussian Naive Bayes** expert;
- out-of-fold Platt calibration;
- competence coordinates derived from expert disagreement and entropy differences;
- a hierarchical Bayesian gate with experiment-level variation;
- posterior integration of the adaptive fusion weight.

<p align="center">
  <img src="figures/29_hbaf_internal_architecture.png" width="880" alt="HBAF internal architecture">
</p>

## Repository structure

```text
bayesian-milling-monitoring-hbaf/
├── dataset/
│   ├── README.md
│   ├── dataset_manifest.csv
│   └── download_msm_subset.py
├── notebooks/
│   ├── 01_dataset_audit_and_classic_eda.ipynb
│   ├── 02_advanced_data_analysis_feature_engineering_and_splits.ipynb
│   ├── 03_competitive_models.ipynb
│   ├── 04_bayesian_adaptive_hybrid_development.ipynb
│   ├── 05_statistical_robustness_and_uncertainty.ipynb
│   └── 06_final_internal_external_evaluation.ipynb
├── artifacts/       # compact CSV evidence used by the study/manuscript
├── figures/         # manuscript and supplementary/reviewer figures
├── requirements.txt
└── README.md
```

The notebooks contain the scientific code and retained textual/tabular outputs of the frozen research run. Large embedded PNG notebook outputs are intentionally not duplicated because the corresponding publication figures are stored separately in `figures/`.

## Dataset

| Domain | Role | Cutting paths | Independent experiments |
|---|---|---:|---:|
| `imi_vmx30ui` | Development | 927 | 19 |
| `imi_vm20i` | Cross-machine evaluation pool | 1,585 | 37 |

Primary target:

- `0`: continue machining (`Normal`)
- `1`: intervention required (`Abnormal` or `Tool defect`)

The statistical unit is an **annotated cutting path**, not an individual MTConnect row.

Dataset DOI: **https://doi.org/10.34740/kaggle/ds/8392825**

To avoid duplicating a third-party public dataset in Git history, the repository records the exact 115-file research subset and SHA-256 checksums in `dataset/dataset_manifest.csv`. Run:

```bash
python dataset/download_msm_subset.py
```

to materialize and verify the required MTConnect CSV files, expert labels, XML information models, and `dataset_summary.xlsx` under `dataset/raw/`.

## Leakage-safe experimental protocol

1. Experiment-disjoint train/validation/internal-test roles.
2. Cross-machine separation for `imi_vm20i`.
3. Causal path prefixes at 25%, 50%, 75%, and 100%.
4. Fold-local cleaning and exact-duplicate removal.
5. Fold-local mutual-information Top-64 selection.
6. Training-fold-only imputation and scaling.
7. Inner-OOF probability calibration and operating-threshold selection.
8. No test/external-label use for architecture tuning.

## Competitive models

The benchmark covers complementary model families rather than only weak baselines: Elastic-Net logistic regression, Random Forest, Extra Trees, HistGradientBoosting, XGBoost, LightGBM, CatBoost, Gaussian/Quantile Naive Bayes, static/dynamic Bayesian networks, Tabular ResNet, TabM, FT-Transformer, Causal TCN, InceptionTime, and PatchTST-style models.

## Development OOF snapshot

| Model | MCC | PR-AUC | AUROC | Macro-F1 | Brier | NLL | ECE |
|---|---:|---:|---:|---:|---:|---:|---:|
| **HBAF** | 0.6383 | 0.8552 | 0.9548 | 0.8126 | 0.0773 | 0.2420 | 0.0585 |
| TabM calibrated | 0.5437 | 0.8538 | 0.9376 | 0.7643 | 0.0877 | 0.3389 | 0.0736 |
| GaussianNB calibrated | 0.5444 | 0.6764 | 0.9232 | 0.7645 | 0.0944 | 0.2947 | 0.0818 |
| Equal fusion | 0.6175 | 0.8609 | 0.9557 | 0.8013 | 0.0737 | 0.2313 | 0.0500 |
| No hierarchy | 0.6716 | 0.8252 | 0.9452 | 0.8262 | 0.0865 | 0.2776 | 0.0755 |

HBAF shows a strong multi-objective profile, especially in ranking and proper probability scoring. **The repository does not claim universal superiority.** Equal fusion and the no-hierarchy control are better on selected metrics, and multiplicity-controlled paired evidence does not support a general superiority claim.

## Scientific contribution and evidence boundary

The contribution is the **adaptive hierarchical Bayesian fusion mechanism**, not a claim that HBAF must be best on every metric. The current evidence supports competitive discrimination, strong proper probability scores, input-dependent fusion, experiment-aware probabilistic modeling, and transparent negative ablations.

Important limitations are intentionally retained:

- full HBAF is not uniformly best among its architectural controls;
- most paired advantages do not survive multiplicity correction;
- one posterior scale boundary remains unresolved;
- fusion-layer uncertainty is conditional and is not a complete epistemic uncertainty estimate of both experts;
- previously inspected held-out domains are not represented as a newly sealed confirmatory test after iterative development.

## Reproduction

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python dataset/download_msm_subset.py
jupyter lab
```

Run the notebooks strictly in order:

```text
01 → 02 → 03 → 04 → 05 → 06
```

Notebooks `01` and `02` create processed/unified representations used downstream. Notebooks `03` and `04` train and store competitive/HBAF evidence. Notebook `05` performs statistical, robustness, uncertainty, and decision-support analysis. Notebook `06` is the final evaluation/reporting layer.

### Typography and figures

The notebooks prefer **Times New Roman**. If it is unavailable, they fall back to Liberation Serif, Nimbus Roman, or DejaVu Serif while preserving the scientific layout. Figure-generation code uses Matplotlib and 350-DPI publication settings.

- `figures/1_...png` through `figures/31_...png`: main-manuscript figures.
- `figures/S1_...png` through `figures/S7_...png`: supplementary/reviewer-facing figures.

## Artifacts

`artifacts/` contains compact CSV evidence required to reproduce manuscript tables and verify the reported analysis: data-quality summaries, split/leakage checks, domain-shift diagnostics, competitive-model configurations/results, HBAF component metrics, paired statistics, risk-coverage, decision curves, efficiency, and evidence-boundary summaries.

Intermediate caches, model binaries, OS metadata, technical QA logs, and obsolete HBARF development artifacts are intentionally excluded.

## Data license and citation

The MSM dataset is distributed under **CC BY 4.0** according to the data descriptor. Please cite:

> Kim, E., Sim, Y., Li, A. S., et al. *Multi-sensor and MTConnect dataset of metal cutting anomaly in milling from laboratory and industry settings*. Scientific Data 13, 945 (2026). https://doi.org/10.1038/s41597-026-07255-7

Dataset DOI: https://doi.org/10.34740/kaggle/ds/8392825

## Reproducibility note

This repository is a research artifact accompanying a scientific study. Reported notebook outputs are frozen results of the stated protocol. Re-running deep-learning components can vary with library versions and hardware; fixed seeds and experiment-disjoint folds are retained to reduce avoidable variation.

## Status

**Research code and evidence package.** The project supports a scientific claim of a competitive Bayesian-hybrid monitoring approach with explicit uncertainty and robustness analysis. It does **not** claim universal model superiority or journal acceptance.
