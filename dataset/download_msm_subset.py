from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import kagglehub
import pandas as pd

DATASET_DIR = Path(__file__).resolve().parent
RAW = DATASET_DIR / "raw"
MANIFEST = DATASET_DIR / "dataset_manifest.csv"
KAGGLE_SLUG = "manufuturetoday/multi-sensor-for-metal-milling-anomaly"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_source(download_root: Path, relative_path: str) -> Path:
    direct = download_root / relative_path
    if direct.exists():
        return direct
    name = Path(relative_path).name
    matches = [p for p in download_root.rglob(name) if p.is_file()]
    if len(matches) == 1:
        return matches[0]
    rel_parts = Path(relative_path).parts
    scored = []
    for p in matches:
        parts = p.parts
        score = 0
        for a, b in zip(reversed(parts), reversed(rel_parts)):
            if a != b:
                break
            score += 1
        scored.append((score, p))
    if scored:
        scored.sort(key=lambda x: (-x[0], str(x[1])))
        if len(scored) == 1 or scored[0][0] > scored[1][0]:
            return scored[0][1]
    raise FileNotFoundError(f"Could not uniquely locate {relative_path!r} under {download_root}")


def main() -> None:
    manifest = pd.read_csv(MANIFEST)
    print(f"Downloading public MSM dataset: {KAGGLE_SLUG}")
    download_root = Path(kagglehub.dataset_download(KAGGLE_SLUG)).resolve()
    RAW.mkdir(parents=True, exist_ok=True)

    for row in manifest.itertuples(index=False):
        rel = str(row.relative_path)
        src = resolve_source(download_root, rel)
        dst = RAW / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or sha256(dst) != str(row.sha256):
            shutil.copy2(src, dst)
        actual = sha256(dst)
        if actual != str(row.sha256):
            raise RuntimeError(
                f"Checksum mismatch: {rel}\nexpected={row.sha256}\nactual={actual}"
            )

    print(f"PASS: materialized and verified {len(manifest)} required raw files in {RAW}")


if __name__ == "__main__":
    main()
