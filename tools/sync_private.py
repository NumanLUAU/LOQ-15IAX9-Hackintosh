"""Mirror EFI/ into EFI-private/ (gitignored) and put my real SMBIOS into the private copies.

EFI/ and profiles/ are the public, blank-SMBIOS versions that go in git. EFI-private/ is what I actually copy to my USB or ESP.
Run after changing anything in EFI/ or profiles/:   python -I tools/sync_private.py
The real values live in private_smbios.json (gitignored): {"model","serial","mlb","uuid","rom"}.
"""
import json, os, plistlib, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB, PRIV = os.path.join(ROOT, "EFI"), os.path.join(ROOT, "EFI-private")
smb = json.load(open(os.path.join(ROOT, "private_smbios.json")))

def inject(src, dst):
    p = plistlib.load(open(src, "rb")); g = p["PlatformInfo"]["Generic"]
    g.update(SystemProductName=smb["model"], SystemSerialNumber=smb["serial"], MLB=smb["mlb"],
             SystemUUID=smb["uuid"], ROM=bytes.fromhex(smb["rom"]))
    plistlib.dump(p, open(dst, "wb"), sort_keys=False)

# mirror EFI -> EFI-private/EFI-contents (everything except OC/config.plist)
for d, _, files in os.walk(PUB):
    rel = os.path.relpath(d, PUB)
    os.makedirs(os.path.join(PRIV, rel), exist_ok=True)
    for f in files:
        if rel == "OC" and f == "config.plist":
            continue
        s, t = os.path.join(d, f), os.path.join(PRIV, rel, f)
        if not os.path.exists(t) or open(s, "rb").read() != open(t, "rb").read():
            shutil.copy2(s, t)
# remove files that no longer exist in EFI/
for d, _, files in os.walk(PRIV, topdown=False):
    rel = os.path.relpath(d, PRIV)
    if rel.split(os.sep)[0] == "profiles":
        continue
    for f in files:
        if not os.path.exists(os.path.join(PUB, rel, f)) and not (rel == "OC" and f == "config.plist"):
            os.remove(os.path.join(d, f))
    if rel != "." and not os.listdir(d):
        os.rmdir(d)
inject(os.path.join(PUB, "OC", "config.plist"), os.path.join(PRIV, "OC", "config.plist"))
# profiles
os.makedirs(os.path.join(PRIV, "profiles"), exist_ok=True)
for f in os.listdir(os.path.join(ROOT, "profiles")):
    if f.endswith(".plist"):
        inject(os.path.join(ROOT, "profiles", f), os.path.join(PRIV, "profiles", f))
print("EFI-private synced with EFI (real SMBIOS injected into config.plist and profiles)")
