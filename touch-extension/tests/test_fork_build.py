#!/usr/bin/env python3
"""Fork preparation lifecycle: preserve originals and reject edited build copies."""
import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_firmware


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / "tmp")
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "upstream-reference", self.root / "upstream-reference")
        self.patch = patch.object(prepare_firmware, "ROOT", self.root)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def prepare(self):
        with contextlib.redirect_stdout(io.StringIO()):
            prepare_firmware.prepare()

    def test_repeat_preserves_originals_and_archives_generated_copy(self):
        source = prepare_firmware.REPO / "HeishaMon/HeishaMon.ino"
        before = source.read_bytes()
        self.prepare()
        first = (self.root / "firmware/HeishaMon/HeishaMon.ino").read_bytes()
        self.assertIn(b"hmxLoop();", first)
        self.prepare()
        self.assertEqual(first, (self.root / "firmware/HeishaMon/HeishaMon.ino").read_bytes())
        self.assertEqual(before, source.read_bytes())
        self.assertEqual(1, len(list((self.root / "archive").iterdir())))

    def test_edited_generated_sketch_is_preserved(self):
        self.prepare()
        generated = self.root / "firmware/HeishaMon/HeishaMon.ino"
        edited = generated.read_bytes() + b"\n// local edit\n"
        generated.write_bytes(edited)
        with self.assertRaisesRegex(ValueError, "local edits"):
            self.prepare()
        self.assertEqual(edited, generated.read_bytes())

    def test_wrong_baseline_fails_before_any_output(self):
        path = self.root / "upstream-reference/tree.json"
        data = json.loads(path.read_text())
        data["files"][0]["sha"] = "0" * 40
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "reviewed baseline"):
            self.prepare()
        self.assertFalse((self.root / "firmware").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
