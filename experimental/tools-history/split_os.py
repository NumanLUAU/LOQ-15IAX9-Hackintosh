"""One-off: split the single EFI into EFI-Tahoe (current) and EFI-Sequoia (the one that worked before the Tahoe update).

  EFI/ -> EFI-Tahoe/, EFI-private/ -> EFI-private-Tahoe/, profiles/*.plist -> profiles/Tahoe/
  EFI-Sequoia/ = backups/pre-tahoe-update/EFI without the Tahoe-only pieces (iBridged, -ibtcompatbeta)
"""
import copy, os, plistlib, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
G = "7C436110-AB2A-4BBB-A880-FE41995C9F82"

# Tahoe
if os.path.isdir("EFI") and not os.path.isdir("EFI-Tahoe"):
    os.rename("EFI", "EFI-Tahoe")
if os.path.isdir("EFI-private") and not os.path.isdir("EFI-private-Tahoe"):
    os.rename("EFI-private", "EFI-private-Tahoe")
os.makedirs("profiles/Tahoe", exist_ok=True)
os.makedirs("profiles/Sequoia", exist_ok=True)
for f in os.listdir("profiles"):
    src = os.path.join("profiles", f)
    if os.path.isfile(src) and f.endswith(".plist"):
        dst = "profiles/Tahoe"
        shutil.move(src, os.path.join(dst, f))

# Sequoia
if os.path.exists("EFI-Sequoia"):
    shutil.rmtree("EFI-Sequoia")
shutil.copytree("backups/pre-tahoe-update/EFI", "EFI-Sequoia")
shutil.rmtree("EFI-Sequoia/OC/Kexts/iBridged.kext", ignore_errors=True)
for junk in ("SimpleHDA.kext",):
    shutil.rmtree(f"EFI-Sequoia/OC/Kexts/{junk}", ignore_errors=True)
p = plistlib.load(open("EFI-Sequoia/OC/config.plist", "rb"))
p["Kernel"]["Add"] = [k for k in p["Kernel"]["Add"] if k["BundlePath"] not in ("iBridged.kext", "SimpleHDA.kext")]
n = p["NVRAM"]["Add"][G]
n["boot-args"] = " ".join(a for a in n["boot-args"].split() if a not in ("-ibtcompatbeta", "revpatch=sbvmm"))
p["Misc"]["Boot"]["HideAuxiliary"] = True
for k in p["Kernel"]["Add"]:
    if k["BundlePath"] == "AirportItlwm.kext":
        k["Comment"] = "Intel AX203 native Wi-Fi. v2.4.0 build from the pranish-dev/loq_hackintosh EFI (the official Sonoma 14.4 build fails vtable patching on Sequoia). Sequoia only"
        k["MinKernel"], k["MaxKernel"] = "24.0.0", "24.99.99"
g = p["PlatformInfo"]["Generic"]
g.update(MLB="M0000000000000001", SystemSerialNumber="W00000000001",
         SystemUUID="00000000-0000-0000-0000-000000000000", ROM=bytes(6))
plistlib.dump(p, open("EFI-Sequoia/OC/config.plist", "wb"), sort_keys=False)

d = "profiles/Sequoia"
plistlib.dump(copy.deepcopy(p), open(f"{d}/config-NVIDIA-only-dual-display.plist", "wb"), sort_keys=False)
q = copy.deepcopy(p)
q["Misc"]["Boot"]["Timeout"] = 5
plistlib.dump(q, open(f"{d}/config-daily-quiet-autoboot.plist", "wb"), sort_keys=False)
b = copy.deepcopy(p)
bn = b["NVRAM"]["Add"][G]
bn["boot-args"] = "-v keepsyms=1 debug=0x100 msgbuf=1048576 " + bn["boot-args"]
b["Misc"]["Debug"].update(Target=0x41, AppleDebug=True, ApplePanic=True, DisplayLevel=0x80000042)
plistlib.dump(b, open(f"{d}/config-debug-verbose.plist", "wb"), sort_keys=False)

subprocess.run([sys.executable, "-I", "tools/sync_private.py"], check=True)
print("split done")
