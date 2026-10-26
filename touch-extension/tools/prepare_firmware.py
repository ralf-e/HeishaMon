#!/usr/bin/env python3
"""Generate an isolated HMX sketch from the reviewed upstream checkout."""
import hashlib
import io
import subprocess
import tarfile
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def normalized(path):
    # Git for Windows may check out the reviewed text sources with CRLF.
    return path.read_bytes().replace(b"\r\n", b"\n")


def prepare():
    baseline = json.loads((ROOT / "upstream-reference/tree.json").read_text())
    archive_bytes = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "archive", "--format=tar", baseline["commit"], "HeishaMon"],
        cwd=REPO, check=True, stdout=subprocess.PIPE).stdout
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
        sources = {item["path"]: archive.extractfile(item["path"]).read()
                   for item in baseline["files"]}
    for item in baseline["files"]:
        data = sources[item["path"]]
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if (blob != item["sha"] or normalized(REPO / item["path"])
                != data.replace(b"\r\n", b"\n")):
            raise ValueError("Upstream source differs from reviewed baseline: " + item["path"]
                             + "; review the upstream update before building")
    destination = ROOT / "firmware"
    if destination.is_symlink():
        raise ValueError("Refusing a linked firmware directory")
    if destination.exists():
        state = json.loads((destination / "hmx-prepared.json").read_text())
        for path, expected in state["files"].items():
            if sha((destination / path).read_bytes()) != expected:
                raise ValueError("Generated sketch has local edits: " + path
                                 + "; preserve these changes before preparing again")
    temporary = ROOT / "tmp"
    temporary.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prepare-", dir=temporary) as temp:
        stage = Path(temp) / "firmware"
        # Only copy reviewed source files, never old Arduino build output.
        for item in baseline["files"]:
            target = stage / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(sources[item["path"]])
        import apply_extension
        apply_extension.run(stage)
        hashes = {p.relative_to(stage).as_posix(): sha(p.read_bytes())
                  for p in stage.rglob("*") if p.is_file()}
        (stage / "hmx-prepared.json").write_text(json.dumps(
            {"baseline": baseline["commit"], "files": hashes}, indent=2) + "\n")
        if destination.exists():
            archive = ROOT / "archive"
            archive.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            destination.rename(archive / ("generated-" + stamp))
        stage.rename(destination)
    print("Prepared: " + str(destination / "HeishaMon/HeishaMon.ino"))
    print("Upstream originals unchanged; baseline " + baseline["commit"])


if __name__ == "__main__":
    try:
        prepare()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit("STOP: " + str(error))
