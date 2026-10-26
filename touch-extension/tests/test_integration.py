#!/usr/bin/env python3
import contextlib, hashlib, importlib.util, io, json, shutil, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("overlay",ROOT/"tools/apply_extension.py")
overlay=importlib.util.module_from_spec(spec);spec.loader.exec_module(overlay)
class IntegrationTests(unittest.TestCase):
    def setUp(self):
        (ROOT/"tmp/tests").mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/"tmp/tests");self.p=Path(self.tmp.name)
        (self.p/"HeishaMon").mkdir()
        for f in ("HeishaMon.ino","gpio.cpp"):
            shutil.copyfile(ROOT/"upstream-reference"/f,self.p/"HeishaMon"/f)
    def tearDown(self):self.tmp.cleanup()
    def run_quiet(self,check=False):
        with contextlib.redirect_stdout(io.StringIO()):overlay.run(self.p,check)
    def test_dry_run_does_not_write(self):
        before=(self.p/"HeishaMon/HeishaMon.ino").read_bytes()
        self.run_quiet(True)
        self.assertEqual(before,(self.p/"HeishaMon/HeishaMon.ino").read_bytes())
        self.assertFalse((self.p/"hmx-installed.json").exists())
    def test_apply_and_idempotence(self):
        self.run_quiet();before={str(p):p.read_bytes() for p in self.p.rglob("*") if p.is_file()}
        self.run_quiet()
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.p.rglob("*") if p.is_file()})
        s=(self.p/"HeishaMon/HeishaMon.ino").read_text()
        self.assertIn("hmxTxLock();",s);self.assertIn("hmxTxUnlock();",s)
        self.assertIn("hmxRx(0);",s);self.assertIn("hmxRx(1);",s);self.assertIn("hmxRx(2);",s)
        self.assertIn("HMX_PASSIVE",s);self.assertNotIn("digitalWrite(ENABLEPIN, HIGH);",s)
    def test_changed_anchor_stops_before_writing(self):
        f=self.p/"HeishaMon/gpio.cpp";f.write_text(f.read_text().replace("    pinMode(","    pinMode_CHANGED("))
        before={str(p):p.read_bytes() for p in self.p.rglob("*") if p.is_file()}
        with self.assertRaises(ValueError):self.run_quiet()
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.p.rglob("*") if p.is_file()})
    def test_edited_install_is_not_overwritten(self):
        self.run_quiet();f=self.p/"HeishaMon/src/hmx/hmx_config.h";f.write_text(f.read_text()+"\n// local edit\n")
        with self.assertRaises(ValueError):self.run_quiet()
    def test_partial_install_is_rejected(self):
        f=self.p/"HeishaMon/gpio.cpp";f.write_text(f.read_text()+"\n"+overlay.MARK)
        with self.assertRaises(ValueError):self.run_quiet()
    def test_catalogue_counts(self):
        h=(ROOT/"firmware/HeishaMon/decode.h").read_text()
        import re
        for macro,array in [("NUMBER_OF_TOPICS","topics"),("NUMBER_OF_TOPICS_EXTRA","xtopics"),("NUMBER_OF_OPT_TOPICS","optTopics")]:
            n=int(re.search(r"#define "+macro+r"\s+(\d+)",h)[1])
            body=re.search(r"static const char "+array+r"\[.*?\]\s+PROGMEM\s*=\s*\{(.*?)\};",h,re.S)[1]
            self.assertEqual(n,len(re.findall(r'"[^"]+"',body)))
if __name__=="__main__":unittest.main(verbosity=2)
