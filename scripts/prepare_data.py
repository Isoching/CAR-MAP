"""Restore losslessly compressed V7 files and verify their original SHA-256 hashes."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare() -> dict:
    manifest = json.loads((ROOT / "PACKAGING.json").read_text(encoding="utf-8"))
    restored = 0
    for record in manifest["compressed_files"]:
        source = ROOT / record["gzip_path"]
        target = ROOT / record["path"]
        if not source.resolve().is_relative_to(ROOT) or not target.resolve().is_relative_to(ROOT):
            raise ValueError("A packaging path escapes the repository")
        if sha256(source) != record["gzip_sha256"]:
            raise ValueError(f"Compressed-file checksum mismatch: {record['gzip_path']}")
        if target.exists():
            if sha256(target) != record["sha256"]:
                raise ValueError(f"Local file differs from frozen V7 data: {record['path']}")
            continue
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
                temporary = Path(output.name)
                with gzip.open(source, "rb") as stream:
                    shutil.copyfileobj(stream, output)
            if sha256(temporary) != record["sha256"]:
                raise ValueError(f"Decompressed-file checksum mismatch: {record['path']}")
            temporary.replace(target)
            restored += 1
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    archive = ROOT / "datasets" / manifest["source_archive"]
    if sha256(archive) != manifest["source_archive_sha256"]:
        raise ValueError("Original source-data ZIP checksum mismatch")
    return {"status": "PASS", "compressed_files_verified": len(manifest["compressed_files"]),
            "files_restored": restored, "original_zip_verified": True}


if __name__ == "__main__":
    print(json.dumps(prepare(), indent=2))
