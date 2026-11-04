"""Update the public EFI/ for macOS Tahoe from the EFI that actually booted Tahoe (TahoeEFIBrokenWifi/OC), then sync EFI-private.

What it does (run from the repo root:  python -I tools/update_tahoe.py):
  1. backs up EFI/ and EFI-private/ to backups/pre-tahoe-update/ (gitignored)
  2. takes config.plist from the Tahoe EFI, blanks the SMBIOS values, HideAuxiliary back to true
  3. replaces three kexts with the exact releases I downloaded into dl/:
       RestrictEvents 1.1.6 RELEASE, iBridged 1.0.1 RELEASE, AirportItlwm (laobamac Tahoe 2.4.0 alpha)
  4. makes sure -ibtcompatbeta and revpatch=sbvmm are in boot-args
  5. regenerates the quiet / autoboot / debug profiles from the new config and runs tools/sync_private.py
"""
import copy, os, plistlib, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
G = "7C436110-AB2A-4BBB-A880-FE41995C9F82"

SRC = {
    "RestrictEvents.kext": "dl/RestrictEvents-1.1.6-RELEASE/x/RestrictEvents.kext",
    "iBridged.kext": "dl/iBridged-1.0.1-RELEASE/x/iBridged.kext",
    "AirportItlwm.kext": "dl/laobamac-itlwm/x/AirportItlwm.kext",
}

# 1. backups
bk = "backups/pre-tahoe-update"
if not os.path.exists(bk):
    os.makedirs(bk)
    shutil.copytree("EFI", f"{bk}/EFI")
    shutil.copytree("EFI-private", f"{bk}/EFI-private")

# 2. kexts
for name, src in SRC.items():
    dst = f"EFI/OC/Kexts/{name}"
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

# 3. config from the EFI that booted Tahoe
p = plistlib.load(open("TahoeEFIBrokenWifi/OC/config.plist", "rb"))
g = p["PlatformInfo"]["Generic"]
g.update(MLB="M0000000000000001", SystemSerialNumber="W00000000001",
         SystemUUID="00000000-0000-0000-0000-000000000000", ROM=bytes(6))
p["Misc"]["Boot"]["HideAuxiliary"] = True
args = p["NVRAM"]["Add"][G]["boot-args"].split()
for a in ("-ibtcompatbeta", "revpatch=sbvmm"):
    if a not in args:
        args.append(a)
p["NVRAM"]["Add"][G]["boot-args"] = " ".join(args)
for k in p["Kernel"]["Add"]:
    if k["BundlePath"] == "AirportItlwm.kext":
        k["Comment"] = "Intel AX203 native Wi-Fi, laobamac itlwm v2.4.0 alpha Tahoe build (needs no OCLP root patches). Fallback: itlwm.kext + HeliPort"
    if k["BundlePath"] == "iBridged.kext":
        k["Comment"] = "Lilu plugin that fixes macOS OTA updates (BridgeOSInstall)"
    if k["BundlePath"] == "RestrictEvents.kext":
        k["Comment"] = "CPU name for the spoofed CPUID (RELEASE 1.1.6)"
plistlib.dump(p, open("EFI/OC/config.plist", "wb"), sort_keys=False)

# 4. profiles
drop = {"-v", "keepsyms=1", "debug=0x100", "msgbuf=1048576"}
shipped = copy.deepcopy(p)
plistlib.dump(shipped, open("profiles/config-NVIDIA-only-dual-display.plist", "wb"), sort_keys=False)
quiet = copy.deepcopy(p)
quiet["Misc"]["Boot"]["Timeout"] = 5
plistlib.dump(quiet, open("profiles/config-daily-quiet-autoboot.plist", "wb"), sort_keys=False)
dbg = copy.deepcopy(p)
n = dbg["NVRAM"]["Add"][G]
n["boot-args"] = "-v keepsyms=1 debug=0x100 msgbuf=1048576 " + n["boot-args"]
dbg["Misc"]["Debug"].update(Target=0x41, AppleDebug=True, ApplePanic=True)
plistlib.dump(dbg, open("profiles/config-debug-verbose.plist", "wb"), sort_keys=False)

# 5. private copy
subprocess.run([sys.executable, "-I", "tools/sync_private.py"], check=True)
print("updated EFI/, profiles/ and EFI-private/")
