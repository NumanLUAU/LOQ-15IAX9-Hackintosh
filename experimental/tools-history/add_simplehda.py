"""Tahoe audio + Wi-Fi kext limits. Run from the repo root:  python -I tools/add_simplehda.py

* adds SimpleHDA 1.0.0 (laobamac, Lilu plugin that restores AppleHDA on macOS Tahoe) right after AppleALC, Tahoe only (Darwin 25.x)
* limits AirportItlwm (Tahoe build) to Darwin 25.x, as its README asks when Sequoia and Tahoe share a config
* regenerates the quiet / autoboot / debug profiles from the new public config and syncs EFI-private
"""
import copy, hashlib, json, os, plistlib, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
G = "7C436110-AB2A-4BBB-A880-FE41995C9F82"
SRC = "dl/SimpleHDA/x/SimpleHDA-Tahoe-v1.0.0-RELEASE"

# integrity check against the release's own SHA256.json
sums = json.load(open(f"{SRC}/SHA256.json"))
for rel, want in sums.items():
    f = os.path.join(SRC, rel)
    if os.path.isfile(f):
        got = hashlib.sha256(open(f, "rb").read()).hexdigest()
        assert got == want, f"checksum mismatch for {rel}"

dst = "EFI/OC/Kexts/SimpleHDA.kext"
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(f"{SRC}/SimpleHDA.kext", dst)

p = plistlib.load(open("EFI/OC/config.plist", "rb"))
add = [k for k in p["Kernel"]["Add"] if k["BundlePath"] != "SimpleHDA.kext"]
i = [k["BundlePath"] for k in add].index("AppleALC.kext")
add.insert(i + 1, {
    "Arch": "x86_64", "BundlePath": "SimpleHDA.kext",
    "Comment": "SimpleHDA 1.0.0: restores AppleHDA on Tahoe (needs AppleALC before it and keepsyms=1). Tahoe only",
    "Enabled": True, "ExecutablePath": "Contents/MacOS/SimpleHDA", "MaxKernel": "25.99.99", "MinKernel": "25.0.0",
    "PlistPath": "Contents/Info.plist"})
for k in add:
    if k["BundlePath"] == "AirportItlwm.kext":
        k["MinKernel"], k["MaxKernel"] = "25.0.0", "25.99.99"
p["Kernel"]["Add"] = add
args = p["NVRAM"]["Add"][G]["boot-args"].split()
assert "keepsyms=1" in args
plistlib.dump(p, open("EFI/OC/config.plist", "wb"), sort_keys=False)

shipped = copy.deepcopy(p)
plistlib.dump(shipped, open("profiles/config-NVIDIA-only-dual-display.plist", "wb"), sort_keys=False)
quiet = copy.deepcopy(p)
quiet["Misc"]["Boot"]["Timeout"] = 5
plistlib.dump(quiet, open("profiles/config-daily-quiet-autoboot.plist", "wb"), sort_keys=False)
dbg = copy.deepcopy(p)
n = dbg["NVRAM"]["Add"][G]
n["boot-args"] = "-v debug=0x100 msgbuf=1048576 " + n["boot-args"]
dbg["Misc"]["Debug"].update(Target=0x41, AppleDebug=True, ApplePanic=True, DisplayLevel=0x80000042)
plistlib.dump(dbg, open("profiles/config-debug-verbose.plist", "wb"), sort_keys=False)

subprocess.run([sys.executable, "-I", "tools/sync_private.py"], check=True)
print("SimpleHDA added, AirportItlwm limited to Darwin 25.x, profiles and EFI-private synced")
