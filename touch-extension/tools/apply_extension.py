#!/usr/bin/env python3
"""Apply the maintained HMX overlay to an upstream checkout, without fuzzy edits."""
import argparse, hashlib, json, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MARK = "// HMX integration v1"
def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise ValueError(f"{label}: expected one anchor, found {n}; no files changed")
    return text.replace(old, new, 1)
def transform_ino(s):
    start = s.index("  //try to detect if cz-taw1 is connected in parallel")
    end = s.index("\n}\n\nvoid setupMqtt()", start)
    s = s[:start] + """#if defined(ESP32) && HMX_ENABLED
  hmxBegin(heatpumpSerial.available() > 0);
#else
""" + s[start:end] + """\n#endif""" + s[end:]
    # Keep the original ESP8266 implementation; only rewrite the ESP32-enabled path
    # via a common expression macro. The old boot assignment must stay writable.
    oldboot = "      heishamonSettings.listenonly = true;"
    s = s.replace(oldboot,"      HMX_BOOT_SETTING = true;")
    s = s.replace("heishamonSettings.listenonly", "HMX_PASSIVE")
    s = s.replace("HMX_BOOT_SETTING","heishamonSettings.listenonly")
    include = """#include "hmx.h"
#if defined(ESP32) && HMX_ENABLED
#define HMX_PASSIVE hmxListenOnly()
#define HMX_ENABLE_WRITE(value) hmxWriteEnable(value)
#else
#define HMX_PASSIVE heishamonSettings.listenonly
#define HMX_ENABLE_WRITE(value) digitalWrite(ENABLEPIN, value)
#endif
""" + MARK + "\n"
    s = replace_once(s, '#include "version.h"\n', '#include "version.h"\n'+include, "include")
    s = s.replace("digitalWrite(ENABLEPIN, LOW);","HMX_ENABLE_WRITE(LOW);")
    s = s.replace("digitalWrite(ENABLEPIN, HIGH);","HMX_ENABLE_WRITE(HIGH);")
    s = replace_once(s, "  loadSettings(&heishamonSettings);",
        "  loadSettings(&heishamonSettings);\n  hmxEarly();", "early CS")
    s = replace_once(s, "  inSetup = false;", "  hmxDisplayBegin();\n  inSetup = false;", "display setup")
    s = replace_once(s, "void loop() {", "void loop() {\n  hmxLoop();", "loop")
    # TX task owns each iteration under the same recursive mutex as mode transitions.
    a=s.index("void serialTXTask("); b=s.index("\n#else\n",a)
    part=s[a:b]
    part=replace_once(part,"    unsigned long now = millis();",
                     "    hmxTxLock();\n    unsigned long now = millis();","TX lock")
    part=replace_once(part,"    vTaskDelay(1 / portTICK_PERIOD_MS);",
                     "    hmxTxUnlock();\n    vTaskDelay(1 / portTICK_PERIOD_MS);","TX unlock")
    part=replace_once(part,"bool send_command(byte* command, int length) {",
                     """bool send_command(byte* command, int length) {
  struct HmxCommandGuard {
    HmxCommandGuard() { hmxTxLock(); }
    ~HmxCommandGuard() { hmxTxUnlock(); }
  } hmxCommandGuard;""","enqueue lock")
    s=s[:a]+part+s[b:]
    for b,call in enumerate([
      "decode_heatpump_data(data, actData, mqtt_client, log_message, heishamonSettings.mqtt_topic_base, heishamonSettings.updateAllTime);",
      "decode_heatpump_data_extra(data, actDataExtra, mqtt_client, log_message, heishamonSettings.mqtt_topic_base, heishamonSettings.updateAllTime);",
      "decode_optional_heatpump_data(data, actOptData, mqtt_client, log_message, heishamonSettings.mqtt_topic_base, heishamonSettings.updateAllTime);"]):
        # Timestamp before decoder events so the display can track unchanged frames too.
        s=replace_once(s,call,f"hmxRx({b});\n          "+call,f"RX block {b}")
    return s
def transform_gpio(s):
    s=replace_once(s,'#include "gpio.h"','#include "gpio.h"\n#include "hmx.h"\n'+MARK,"gpio include")
    s=replace_once(s,"    pinMode(gpioSettings.gpioPin[i], gpioSettings.gpioMode[i]);",
       """#if defined(ESP32) && HMX_ENABLED
    if (hmxOwnsPin(gpioSettings.gpioPin[i])) continue;
#endif
    pinMode(gpioSettings.gpioPin[i], gpioSettings.gpioMode[i]);""","reserve GPIOs")
    return s
def run(target, check=False):
    sketch = target / "HeishaMon"
    if not (sketch/"HeishaMon.ino").exists(): raise ValueError("Expected checkout/HeishaMon/HeishaMon.ino")
    paths = ["HeishaMon.ino","gpio.cpp"]
    inputs={p:(sketch/p).read_text(encoding="utf-8") for p in paths}
    marked=[MARK in inputs[p] for p in paths]
    if any(marked):
        if not all(marked): raise ValueError("Partial integration detected; restore clean upstream files")
        # Idempotence is only accepted if every patched source and module matches the manifest.
        manifest=json.loads((target/"hmx-installed.json").read_text())
        for p,h in manifest["installed_sha256"].items():
            actual=hashlib.sha256((target/p).read_bytes()).hexdigest()
            if actual!=h: raise ValueError(f"Changed installed file: {p}; review before reapplying")
        print("HMX already installed; all tracked hashes match");return
    # Validate every anchor and all extension files BEFORE touching the checkout.
    outputs={"HeishaMon.ino":transform_ino(inputs["HeishaMon.ino"]),
             "gpio.cpp":transform_gpio(inputs["gpio.cpp"])}
    source=ROOT/"extension"
    required=["hmx.h","hmx_config.h","hmx.cpp","hmx_policy.h","hmx_choice.h","hmx_status.h","hmx_model.h","hmx_model_data.h"]
    for p in required:
        if not (source/p).is_file():raise ValueError(f"Missing overlay file {p}")
    if check: print("HMX anchors OK; no files changed");return
    tracked={}
    for p,content in outputs.items():
        (sketch/p).write_text(content,encoding="utf-8",newline="\n")
        tracked["HeishaMon/"+p]=hashlib.sha256((sketch/p).read_bytes()).hexdigest()
    for p in required:
        dest=sketch/p if p=="hmx.h" else sketch/"src"/"hmx"/p
        dest.parent.mkdir(parents=True,exist_ok=True)
        # hmx.h in sketch root forwards to the module header.
        if p=="hmx.h":
            dest.write_text('#pragma once\n#include "src/hmx/hmx.h"\n',encoding="utf-8")
            tracked[str(dest.relative_to(target)).replace("\\","/")]=hashlib.sha256(dest.read_bytes()).hexdigest()
            dest=sketch/"src"/"hmx"/p
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/p,dest)
        tracked[str(dest.relative_to(target)).replace("\\","/")]=hashlib.sha256(dest.read_bytes()).hexdigest()
    version=sketch/"version.h"
    # Keep upstream version untouched: extension version is independent.
    (target/"hmx-installed.json").write_text(json.dumps({
      "extension":"0.1.0-dev.7","baseline":"b3ef43691f21985c851903d69a0f2e8647ed31f8",
      "original_sha256":{p:hashlib.sha256(inputs[p].encode()).hexdigest() for p in paths},
      "installed_sha256":tracked},indent=2)+"\n",encoding="utf-8")
    print("HMX installed: 2 upstream files modified; original decode/rules/web files unchanged")
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("checkout",type=Path);ap.add_argument("--check",action="store_true")
    a=ap.parse_args()
    try:run(a.checkout.resolve(),a.check)
    except (ValueError,OSError,KeyError) as e: print("STOP:",e,file=sys.stderr);sys.exit(1)
