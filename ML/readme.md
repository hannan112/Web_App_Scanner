# ML: false-positive reduction

A side project exploring whether a lightweight classifier can flag likely false-positive
findings in the scanner's output, so results can eventually be shown pre-filtered by confidence
rather than as one flat list. This is a research/experimentation track, not yet wired into the
live scanning pipeline — see [Status](#status) below.

## Contents

| File | Purpose |
|---|---|
| `FP_random_forest.ipynb` | Trains a `RandomForestClassifier` on labeled scan findings and saves `fp_confidence_random_forest.pkl`. |
| `apply_fp_model_demo.ipynb` | Loads the trained model and applies it to a single scan's findings, showing before/after filtering. |
| `fp_confidence_random_forest.pkl` | The trained model artifact. |
| `sample_dataset.csv` | A small synthetic dataset (fabricated project/URL data) with the same schema as the real training data, so the training notebook runs end-to-end out of the box. |
| `sample_scan_vulnerabilities.json` | A small synthetic single-scan result, so the demo notebook runs end-to-end out of the box. |

The real dataset used to train the shipped model (~119K rows, collected from scans run under
explicit authorization from the target owners) is **not included** in this repo — those
authorizations covered the scan itself, not public redistribution of the findings. The
synthetic files above exist purely so the notebooks are reproducible without that data; see
[Reproducing with real data](#reproducing-with-real-data) for how to regenerate a real dataset
of your own.

## Methodology

Each vulnerability finding is reduced to a handful of low-dimensional features rather than raw
text, to avoid overfitting on scanner-specific wording:

| Feature | Meaning |
|---|---|
| `has_evidence` | Whether the finding included a concrete evidence string (vs. a bare header/config observation). |
| `is_header_issue` | Whether the finding name matches a curated list of header/config-only findings (often false positives when unaccompanied by evidence). |
| `is_injection` | Whether the finding name matches a curated list of injection/exploit-class findings (SQLi, XSS, etc.) — these are rarely false positives. |

A `RandomForestClassifier` is trained on these features against a weak-supervision label
(`likely_fp`), then outputs a `fp_confidence` probability per finding rather than a hard
delete/keep decision — findings are never discarded outright, only ranked by how likely they
are to be noise.

```
Raw Scan Results
      ↓
Normalization & Cleaning
      ↓
Feature Extraction (has_evidence, is_header_issue, is_injection)
      ↓
ML Inference (fp_confidence, 0-1)
      ↓
Threshold-Based Filtering (default 0.7)
      ↓
Final Results (ranked/filtered, nothing deleted)
```

## Status

This is a standalone experiment: the notebooks demonstrate training and applying the model
against exported scan data, but the backend does not currently call this model automatically
when a scan completes.

### How it would integrate into the live backend

The intended integration point is a post-processing step after results are normalized and
saved, not part of crawling/detection itself:

```
UnifiedScanningEngine
    → normalize_results()
    → deduplicate_results()
    → apply_ml_fp_reduction()   ← integration point
    → save_final_results()
```

Each vulnerability record needs at minimum `name`, `severity`, `url`, `evidence` (optional:
`parameter`, `cwe_id`) — these fields already exist in the scanner's output, so no schema
changes would be required. The classifier would be loaded once (`joblib.load(...)`), features
extracted per finding, and `fp_confidence`/`fp_filtered` persisted back onto each
`Vulnerability` row for auditability. The UI would default to showing filtered results with a
toggle to reveal everything, plus a confidence badge - so an analyst can always override the
model's judgment.

## Reproducing with real data

To retrain against real scan data instead of the synthetic sample:

1. Run scans through the backend against targets you're authorized to test (see
   [`backend/docs/SCANNING_SITES_LIST.md`](../backend/docs/SCANNING_SITES_LIST.md) for safe
   public targets).
2. Export the findings via the scanning app's results API/export into a CSV with columns
   `name,severity,project_name,url,parameter,evidence,cwe_id,has_evidence`.
3. Point `FP_random_forest.ipynb`'s load cell at your exported CSV instead of
   `sample_dataset.csv` and re-run.

## Limitations

- The model's usefulness depends on the scanner's own finding names/wording; retraining is
  needed if the scanner's vulnerability naming changes.
- The `is_header_issue`/`is_injection` feature lists are hand-curated and scanner-specific, not
  learned.
- `likely_fp` is weak-supervision, not human-labeled ground truth - useful as a heuristic prior,
  not a validated benchmark.
