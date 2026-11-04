"""Mirror the public EFIs into the private (gitignored) copies and put my real SMBIOS into the private configs.

  EFI-Tahoe/    EFI-Sequoia/           public, blank SMBIOS values, tracked in git
  profiles/Tahoe/  profiles/Sequoia/   public config variants, blank SMBIOS values
  EFI-private-Tahoe/  EFI-private-Sequoia/   gitignored; identical to the public one except config.plist and profiles carry my real SMBIOS

Run after changing anything in a public EFI or its profiles:   python -I tools/sync_private.py
The real values live in private_smbios.json (gitignored): {"model","serial","mlb","uuid","rom"}.
"""
import json, os, plistlib, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
smb = json.load(open(os.path.join(ROOT, "private_smbios.json")))


def inject(src, dst):
    p = plistlib.load(open(src, "rb"))
    g = p["PlatformInfo"]["Generic"]
    g.update(SystemProductName=smb["model"], SystemSerialNumber=smb["serial"], MLB=smb["mlb"],
             SystemUUID=smb["uuid"], ROM=bytes.fromhex(smb["rom"]))
    plistlib.dump(p, open(dst, "wb"), sort_keys=False)


def same(a, b):
    return os.path.exists(b) and open(a, "rb").read() == open(b, "rb").read()


for name in ("Tahoe", "Sequoia"):
    PUB = os.path.join(ROOT, f"EFI-{name}")
    PRIV = os.path.join(ROOT, f"EFI-private-{name}")
    PROF = os.path.join(ROOT, "profiles", name)
    if not os.path.isdir(PUB):
        continue
    for d, _, files in os.walk(PUB):
        rel = os.path.relpath(d, PUB)
        os.makedirs(os.path.join(PRIV, rel), exist_ok=True)
        for f in files:
            if rel == "OC" and f == "config.plist":
                continue
            s, t = os.path.join(d, f), os.path.join(PRIV, rel, f)
            if not same(s, t):
                shutil.copy2(s, t)
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
    os.makedirs(os.path.join(PRIV, "profiles"), exist_ok=True)
    if os.path.isdir(PROF):
        for f in os.listdir(PROF):
            if f.endswith(".plist"):
                inject(os.path.join(PROF, f), os.path.join(PRIV, "profiles", f))
    print(f"EFI-private-{name} synced with EFI-{name} (real SMBIOS injected into config.plist and profiles)")
