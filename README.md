# Bayesian Milling Monitoring with HBAF

**Hierarchical Bayesian Adaptive Fusion for experiment-aware, probabilistic monitoring of CNC milling.**

> **Publication staging — incomplete file transfer.** This branch updates the scientific documentation, dependencies and compact CSV results. The complete cleaned package has been prepared separately, but its six executable notebooks with scientific outputs, 115 raw inputs, terminal prediction ledgers and complete figure collection have **not yet been transferred to this branch**. Do not treat this branch as a complete executable release. Existing repository assets and history are preserved. The full package contains the final README that replaces this staging notice after transfer.

## Research objective and model

The study evaluates an input-dependent Bayesian fusion mechanism for a derived binary milling-monitoring endpoint. HBAF combines a calibrated **TabM** expert with calibrated **Gaussian Naive Bayes**, using entropy difference and absolute expert disagreement as competence coordinates. A hierarchical gate includes experiment effects; Gaussian coefficient priors, training-only empirical-Bayes scale estimation, a local Laplace approximation and integration over unseen experiment effects define the fusion layer.

The contribution is the probabilistic fusion mechanism and its transparent experimental assessment, **not universal superiority**. Fusion uncertainty is conditional on the fitted experts and estimated scales, rather than a complete uncertainty model for the whole learning system.

## Dataset and scope

The prepared package uses the MTConnect/controller modality from two laboratory machines in the **Multi-Sensor and MTConnect (MSM) dataset**. Audio, video, accelerometer and current-transformer streams that are not used by these notebooks are excluded.

| Machine | Study role | Cutting paths | Experiments |
|---|---|---:|---:|
| `imi_vmx30ui` | Development-machine pool | 927 | 19 |
| `imi_vm20i` | Cross-machine pool | 1,585 | 37 |

The current HBAF experiment uses only **563 development paths from 11 experiments**, with five repeats and three outer experiment-disjoint folds. It evaluates the **100% path checkpoint**. The remaining development-machine pools contain 192 validation and 172 internal-test paths. No current-HBAF internal or cross-machine outcome evaluation is supplied, and previously inspected domains are not newly sealed confirmatory tests. The industrial MSM machine is not included.

The implemented `InterventionRequired` variable equals `(StateLabel > 0)`: it combines abnormal cutting and tool-defect annotations. This is a **composite research target**, not a validated immediate-stop instruction. The original MSM label 2 can describe a defective tool during otherwise normal cutting. See the [original data descriptor](https://doi.org/10.1038/s41597-026-07255-7) and the [sample characterization](artifacts/sample_characterization.csv).

## Development results

Values below are means of complete-repeat OOF metrics in the same matched current cohort. Thresholds are selected inside the development assessment boundaries. PR-AUC follows the average-precision implementation; ECE uses ten fixed equal-width bins.

| Model | MCC ↑ | PR-AUC ↑ | AUROC ↑ | Macro-F1 ↑ | Brier ↓ | NLL ↓ | ECE ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| **HBAF** | 0.6383 | 0.8552 | 0.9548 | 0.8126 | 0.0773 | 0.2420 | 0.0585 |
| TabM calibrated | 0.5437 | 0.8538 | 0.9376 | 0.7643 | 0.0877 | 0.3389 | 0.0736 |
| GaussianNB calibrated | 0.5444 | 0.6764 | 0.9232 | 0.7645 | 0.0944 | 0.2947 | 0.0818 |
| Equal fusion | 0.6175 | 0.8609 | 0.9557 | 0.8013 | 0.0737 | 0.2313 | 0.0500 |
| No hierarchy | 0.6716 | 0.8252 | 0.9452 | 0.8262 | 0.0865 | 0.2776 | 0.0755 |

Source: [current 26-model summary](artifacts/hbaf_current_summary.csv). The 18 benchmark models and eight current variants remain explicitly distinguished by cohort.

HBAF improves several point estimates relative to its calibrated TabM parent. However, equal fusion is better on selected proper scores and ranking metrics; removing hierarchy improves MCC and Macro-F1. The [paired statistical results](artifacts/hbaf_current_statistics.csv) do not establish a general superiority claim. Negative ablations are retained, not filtered out.

### Uncertainty and inferential limits

One main-model fit reaches a numerical scale boundary. Three fits collapse the adaptive coefficient scale and five collapse the hierarchy. A fixed-hyperparameter importance diagnostic uses 4,096 proposals, identifies two modes and obtains an effective sample size of approximately 12.86. It is inconclusive as a posterior-validation reference; credible-risk interval calibration is not established. See [component results](artifacts/hbaf_current_components.csv) and [posterior diagnostics](artifacts/hbaf_current_posterior_diagnostic.csv).

Statistical analysis uses 5,000 paired hierarchical bootstrap draws and all 2,048 experiment-level swap assignments. Multiplicity-adjusted superiority tests and simultaneous noninferiority bounds are not interchangeable. Repeated seeds do not increase the number of independent experiments. Selective-prediction and decision-curve findings remain exploratory.

A bounded-fusion amendment in the supplied notebook record contains four repeats although its protocol specifies five. It remains a separate, incomplete secondary analysis and is not pooled with the completed five-repeat main experiment.

## Prepared publication layout

```text
dataset/raw/         115 original files used by the notebooks
dataset/reference/   terminal OOF predictions and scientific metadata
notebooks/           01 study design → 02 features → 03 benchmarks →
                     04 HBAF → 05 statistical inference → 06 evidence synthesis
artifacts/           32 compact scientific CSV tables
figures/             current workflow figures; older models in legacy/
README.md            complete reproduction instructions and scientific results
```

The cleaned package separates immutable reference inputs from runtime-only `dataset/generated/` products. Notebooks 05 and 06 select `reference` or `generated` evidence explicitly instead of silently mixing model generations. Their reference-mode analyses have been executed end-to-end; the full 01–04 training route has not been re-executed. The scientific data-reading and EDA cells of 01 were executed, but its Parquet persistence step was not. The original training-environment lockfile was not supplied.

The included efficiency aggregate has been recomputed from its supplied per-boundary runtime ledger to resolve a stale source summary. This is an aggregation correction, not a new hardware benchmark.

## Figures and manuscript numbering

The local prepared package retains all 45 archive PNGs: 36 current-workflow images and nine historical images. The manuscript, supplement, reviewer responses and authoritative figure-number map were not supplied. Prefixes such as `01_` and `06_` identify notebook stages; they are **not verified manuscript numbering**. No `1_...` or `S1_...` map is invented. The three previously existing repository illustrations are preserved.

The older `04_hbaf_architecture.png` in the source archive illustrates a Student-t filter, not the current two-expert hierarchical gate. It belongs with legacy figures. Earlier internal/external HBARF plots must not be presented as current-HBAF validation.

## Data attribution and reuse

> Kim, E., Sim, Y., Li, A. S., et al. *Multi-sensor and MTConnect dataset of metal cutting anomaly in milling from laboratory and industry settings*. Scientific Data **13**, 945 (2026). DOI: [10.1038/s41597-026-07255-7](https://doi.org/10.1038/s41597-026-07255-7).

Dataset DOI: [10.34740/kaggle/ds/8392825](https://doi.org/10.34740/kaggle/ds/8392825). The data descriptor identifies the dataset as **CC BY 4.0**. The raw inputs in the prepared package are unchanged subsets. The data license does not automatically license the authors' research software or manuscript. No manuscript DOI, publication status or new software license is inferred.
