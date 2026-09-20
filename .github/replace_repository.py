"""One-time, checksum-pinned replacement of the HBAF repository.

Only the owner can trigger an import, and only the exact prepared archive is
accepted. No code from the archive is executed. A new Git tree is constructed
separately and published with a normal, non-force push after all checks pass.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

REPOSITORY = "Guldek1987/bayesian-milling-monitoring-hbaf"
OWNER_ID = 86553015
THREAD = 1
ARCHIVE_SHA256 = "4a260b1efe886d581a09f805b31123bebbef64e55f4130aa866e25f0c9c7dee8"
ARCHIVE_BYTES = 23842556
ROOT_NAME = "bayesian-milling-monitoring-hbaf"
FILE_COUNT = 211
EXPANDED_BYTES = 72646293
NOTEBOOKS = [
    "01_dataset_characterization_and_study_design.ipynb",
    "02_feature_engineering_and_grouped_splits.ipynb",
    "03_competitive_models.ipynb",
    "04_hbaf_development.ipynb",
    "05_statistical_robustness_and_uncertainty.ipynb",
    "06_development_evidence_synthesis.ipynb",
]
ROOT_ITEMS = {".gitattributes", ".gitignore", "README.md", "requirements.txt",
              "requirements-analysis.txt", "dataset", "notebooks", "artifacts", "figures"}
BOT_ENV = {"GIT_AUTHOR_NAME": "github-actions[bot]",
           "GIT_AUTHOR_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com",
           "GIT_COMMITTER_NAME": "github-actions[bot]",
           "GIT_COMMITTER_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_archive(archive: Path, destination: Path) -> Path:
    require(archive.stat().st_size == ARCHIVE_BYTES, "Unexpected archive size")
    require(digest(archive) == ARCHIVE_SHA256, "Archive SHA-256 does not match the prepared package")
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        require(len(entries) == FILE_COUNT, "Unexpected number of ZIP entries")
        require(sum(entry.file_size for entry in entries) == EXPANDED_BYTES, "Unexpected expanded size")
        seen: set[str] = set()
        for entry in entries:
            path = PurePosixPath(entry.filename)
            require(not entry.is_dir() and not path.is_absolute(), "Unexpected ZIP entry")
            require(path.parts[0] == ROOT_NAME and len(path.parts) > 1, "Unexpected root directory")
            require(not {"..", ".git"}.intersection(path.parts), "Unsafe ZIP path")
            require("\\" not in entry.filename and ":" not in entry.filename, "Unsafe path characters")
            require(path.parts[1] in ROOT_ITEMS, "Unexpected top-level item")
            require((entry.external_attr >> 16) & 0o170000 != 0o120000, "Symlinks are not allowed")
            require(entry.filename not in seen, "Duplicate ZIP path")
            seen.add(entry.filename)
        require(bundle.testzip() is None, "ZIP integrity check failed")
        bundle.extractall(destination)
    root = destination / ROOT_NAME
    files = [path for path in root.rglob("*") if path.is_file()]
    require(len(files) == FILE_COUNT, "Incomplete extraction")
    require({path.name for path in root.iterdir()} == ROOT_ITEMS, "Unexpected repository layout")
    require(sorted(path.name for path in (root / "notebooks").iterdir()) == NOTEBOOKS,
            "The six ordinary .ipynb files are required")
    code_count = 0
    for name in NOTEBOOKS:
        notebook = json.loads((root / "notebooks" / name).read_text(encoding="utf-8"))
        require(notebook.get("nbformat") == 4, f"Invalid notebook format: {name}")
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            source = cell.get("source", "")
            ast.parse("".join(source) if isinstance(source, list) else source)
            require(all(output.get("output_type") != "error" for output in cell.get("outputs", [])),
                    f"Saved error output in {name}")
            code_count += 1
    require(code_count == 311, "Unexpected scientific code-cell count")
    tables = sorted((root / "artifacts").iterdir())
    require(len(tables) == 32 and all(path.suffix == ".csv" for path in tables), "Unexpected artifacts")
    for path in tables:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            require(bool(list(csv.reader(stream))), f"Empty CSV: {path.name}")
    figures = sorted((root / "figures").rglob("*.png"))
    require(len(figures) == 45, "Missing source figures")
    for path in figures:
        with path.open("rb") as stream:
            require(stream.read(8) == b"\x89PNG\r\n\x1a\n", f"Invalid PNG: {path.name}")
    with (root / "dataset" / "dataset_manifest.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 115, "Unexpected raw-data manifest")
    for row in rows:
        path = root / "dataset" / "raw" / row["relative_path"]
        require(path.stat().st_size == int(row["bytes"]), f"Raw-data size mismatch: {row['relative_path']}")
        require(digest(path) == row["sha256"], f"Raw-data checksum mismatch: {row['relative_path']}")
    return root


def git(*args: str, data: bytes | None = None, env: dict[str, str] | None = None) -> str:
    process = subprocess.run(["git", *args], input=data, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env={**os.environ, **BOT_ENV, **(env or {})})
    if process.returncode:
        raise RuntimeError(process.stderr.decode("utf-8", errors="replace"))
    return process.stdout.decode("utf-8").strip()


def repository_context() -> str:
    require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY, "Wrong repository")
    base = git("rev-parse", "HEAD")
    require(base == os.environ["GITHUB_SHA"], "Checkout is not the event snapshot")
    remote = git("ls-remote", "origin", "refs/heads/main").split()[0]
    require(remote == base, "main changed; post a new comment to retry without overwriting concurrent work")
    return base


def write_tree(root: Path, index: Path) -> str:
    env = {"GIT_INDEX_FILE": str(index)}
    git("read-tree", "--empty", env=env)
    index_records = []
    expected = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        sha = git("hash-object", "-w", "--no-filters", "--stdin", data=data)
        expected_sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        require(sha == expected_sha, f"Git changed source bytes: {relative}")
        expected[relative] = sha
        index_records.append(f"100644 {sha}\t{relative}\0")
    git("update-index", "-z", "--index-info", data="".join(index_records).encode(), env=env)
    tree = git("write-tree", env=env)
    actual = {}
    for record in git("ls-tree", "-r", "-z", tree).rstrip("\0").split("\0"):
        metadata, relative = record.split("\t", 1)
        actual[relative] = metadata.split()[2]
    require(actual == expected and len(actual) == FILE_COUNT, "Git tree does not match the complete package")
    return tree


class HTTPSRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        host = parsed.hostname or ""
        require(parsed.scheme == "https" and
                (host == "github.com" or host.endswith((".githubusercontent.com", ".amazonaws.com", ".blob.core.windows.net"))),
                "Unexpected attachment redirect")
        return super().redirect_request(request, fp, code, message, headers, newurl)


def download_attachment(event: dict, path: Path) -> None:
    require(event["issue"]["number"] == THREAD, "Wrong upload thread")
    require(event["comment"]["user"]["id"] == OWNER_ID and event["sender"]["id"] == OWNER_ID,
            "Only the repository owner can authorize replacement")
    candidates = re.findall(r'https://github\.com/[^\s<>"\)]+', event["comment"].get("body", ""))
    urls = []
    for candidate in candidates:
        parsed = urllib.parse.urlparse(candidate)
        if re.fullmatch(r"/(?:user-attachments/files|Guldek1987/bayesian-milling-monitoring-hbaf/files)/[0-9]+/[^/]+\.zip",
                        parsed.path, flags=re.IGNORECASE):
            urls.append(candidate)
    require(len(set(urls)) == 1, "Attach exactly one prepared ZIP to the comment")
    request = urllib.request.Request(urls[0], headers={"User-Agent": "HBAF-repository-importer"})
    opener = urllib.request.build_opener(HTTPSRedirects())
    with opener.open(request, timeout=120) as response, path.open("wb") as output:
        total = 0
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            require(total <= ARCHIVE_BYTES, "Attachment exceeds the expected archive size")
            output.write(chunk)


def preflight() -> None:
    base = repository_context()
    probe = io.BytesIO()
    with zipfile.ZipFile(probe, "w", compression=zipfile.ZIP_LZMA) as bundle:
        bundle.writestr("probe.txt", "HBAF")
    with zipfile.ZipFile(io.BytesIO(probe.getvalue())) as bundle:
        require(bundle.read("probe.txt") == b"HBAF", "ZIP/LZMA is unavailable")
    blob = git("hash-object", "-w", "--stdin", data=b"Temporary HBAF transfer permission test.\n")
    tree = git("mktree", data=f"100644 blob {blob}\tREADME.md\n".encode())
    commit = git("commit-tree", tree, "-p", base, data=b"Test atomic replacement permissions on a temporary branch\n")
    run = os.environ["GITHUB_RUN_ID"]
    require(run.isdigit(), "Invalid run ID")
    branch = f"hbaf-transfer-preflight-{run}-{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
    # The test branch deliberately has no workflow files, like the final package.
    # main is never modified by this test; only this newly created branch is deleted.
    git("push", "origin", f"{commit}:refs/heads/{branch}")
    try:
        require(git("ls-remote", "origin", f"refs/heads/{branch}").split()[0] == commit,
                "Temporary-branch verification failed")
    finally:
        git("push", "origin", f":refs/heads/{branch}")
    require(not git("ls-remote", "origin", f"refs/heads/{branch}"), "Temporary branch was not removed")
    require(git("ls-remote", "origin", "refs/heads/main").split()[0] == base, "main moved during preflight")
    print("Preflight passed: ZIP support, authenticated push, workflow-file removal, temporary-branch cleanup.")
    print("No research files on main were deleted or replaced by this test.")


def apply() -> None:
    base = repository_context()
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    with tempfile.TemporaryDirectory(prefix="hbaf-replace-", dir=os.environ["RUNNER_TEMP"]) as temp:
        work = Path(temp)
        archive = work / "payload.zip"
        download_attachment(event, archive)
        root = validate_archive(archive, work / "extracted")
        tree = write_tree(root, work / "index")
        message = ("Replace repository with the complete HBAF scientific package\n\n"
                   "211 verified files; six scientific notebooks; 115 raw inputs; 32 CSV tables; "
                   "45 original PNGs. Remove packed fragments and all obsolete tracked files. "
                   "Preserve history; do not force-push.\n")
        commit = git("commit-tree", tree, "-p", base, data=message.encode())
        require(git("ls-remote", "origin", "refs/heads/main").split()[0] == base,
                "main changed; replacement was not pushed")
        git("push", "origin", f"{commit}:refs/heads/main")
        require(git("ls-remote", "origin", "refs/heads/main").split()[0] == commit,
                "Post-push verification did not find the expected commit")
        result = {"commit": commit, "tree": tree, "files": FILE_COUNT, "archive_sha256": ARCHIVE_SHA256}
        (Path(os.environ["RUNNER_TEMP"]) / "hbaf-replacement-result.json").write_text(json.dumps(result))
        summary = (f"## Complete repository replacement\n\nCommit: `{commit}`\n\n"
                   "211 files published as ordinary repository files. No `.packed`, archive fragments, "
                   "or temporary import workflows remain in the new tree.\n\n"
                   "This checks file delivery and notebook syntax, not a new full model-training run.\n")
        Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text(summary)
        print(summary)


def report() -> None:
    require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY, "Wrong repository")
    result_file = Path(os.environ["RUNNER_TEMP"]) / "hbaf-replacement-result.json"
    success = result_file.exists() and os.environ.get("IMPORT_STATUS") == "success"
    if success:
        result = json.loads(result_file.read_text())
        body = (f"Полная замена завершена и проверена: **211 обычных файлов** в `main`. "
                f"Коммит: {result['commit']}.\n\n"
                "Шесть `.ipynb`, 115 исходных файлов, 32 CSV-таблицы и 45 PNG загружены. "
                "Все прежние отслеживаемые файлы вне подготовленного пакета удалены из текущего дерева, "
                "включая `.packed` и одноразовый импорт. История сохранена. "
                "Полное обучение заново не запускалось. Нумерация рисунков по рукописи по-прежнему требует самой рукописи. "
                "Этот черновой PR закрывается без слияния: пакет опубликован непосредственно в `main`.")
    else:
        body = ("Импорт не подтвердил полное завершение. Не считайте репозиторий полностью заменённым до успешной проверки. "
                f"Журнал: https://github.com/{REPOSITORY}/actions/runs/{os.environ['GITHUB_RUN_ID']}")
    token = os.environ["GH_TOKEN"]
    def send(endpoint: str, payload: dict, method: str = "POST") -> None:
        request = urllib.request.Request(f"https://api.github.com/repos/{REPOSITORY}/{endpoint}",
            data=json.dumps(payload).encode(), method=method,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json", "User-Agent": "HBAF-repository-importer"})
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
    send(f"issues/{THREAD}/comments", {"body": body})
    if success:
        send(f"pulls/{THREAD}", {"state": "closed"}, method="PATCH")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "check" and len(sys.argv) == 3:
        with tempfile.TemporaryDirectory(prefix="hbaf-check-") as directory:
            root = validate_archive(Path(sys.argv[2]), Path(directory))
            print(f"Verified {FILE_COUNT} files, all raw checksums, notebook syntax, and scientific outputs.")
    elif command in {"preflight", "apply", "report"}:
        {"preflight": preflight, "apply": apply, "report": report}[command]()
    else:
        raise SystemExit("Usage: replace_repository.py check ARCHIVE.zip | preflight | apply | report")
