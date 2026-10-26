#!/usr/bin/env python3
"""Create a named application image only after an actual successful build."""
from pathlib import Path
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument("directory",type=Path);a=p.parse_args()
image=a.directory/"HeishaMon.ino.bin"
data=image.read_bytes()
if not data or data[0]!=0xe9:raise SystemExit("Not an ESP application image")
if len(data)>0x1df000:raise SystemExit("Application exceeds conservative web-OTA limit for min_spiffs")
md5=hashlib.md5(data).hexdigest();sha=hashlib.sha256(data).hexdigest()
name=f"HeishaMon_ESP32-HMX-0.1.0-dev.7-{md5}.bin"
shutil.copyfile(image,a.directory/name)
(a.directory/"firmware_manifest.json").write_text(json.dumps({
"image":name,"size":len(data),"md5":md5,"sha256":sha,
"target":"ESP32-S3","partition":"min_spiffs",
"upstream":"b3ef43691f21985c851903d69a0f2e8647ed31f8","extension":"0.1.0-dev.7",
"hardware_tested":False,"installed_sha256":{path:hashlib.sha256((ROOT/"firmware"/path).read_bytes()).hexdigest() for path in json.loads((ROOT/"firmware/hmx-installed.json").read_text())["installed_sha256"]}},indent=2)+"\n")
print(name)
for notice in ("LICENSE", "LICENSING.md"):
 shutil.copyfile(ROOT/notice,a.directory/notice)
