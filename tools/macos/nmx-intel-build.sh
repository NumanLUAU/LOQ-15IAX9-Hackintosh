#!/bin/bash
# Builds NMIntelFB (nmx-intel patches on NullMoth's kexts/NMIntelFB at v2.3.6). Needs the Xcode Command Line Tools.
# No root needed and nothing on the system changes. Based on the nmx-intel README and tools/intelfb/build.sh.
# Run:  bash nmx-intel-build.sh
set -euo pipefail
ID=${ID:-468b}          # my iGPU, Intel UHD 8086:468B (Alder Lake-S/HX); change for another machine
REV=${REV:-v2.3.6}

xcode-select -p >/dev/null 2>&1 || { echo "Install the Command Line Tools first: xcode-select --install"; exit 1; }
[ -d "$HOME/nmx-intel/.git" ] || git clone https://github.com/kitsuneislife/nmx-intel "$HOME/nmx-intel"
mkdir -p "$HOME/nmx-build"
[ -d "$HOME/nmx-build/nvidia-macos-driver/.git" ] || git clone https://github.com/nullmoth/nvidia-macos-driver "$HOME/nmx-build/nvidia-macos-driver"
git -C "$HOME/nmx-build/nvidia-macos-driver" fetch --tags -q
echo "nmx-intel: $(git -C "$HOME/nmx-intel" log -1 --format='%h %ci')"

# is my iGPU accepted by NMIntelFB at this NullMoth revision?
IDS=$(git -C "$HOME/nmx-build/nvidia-macos-driver" show "$REV:kexts/NMIntelFB/display_ids.inc")
if grep -qi "0x$ID," <<<"$IDS"; then
  echo "OK: iGPU id 0x$ID is in NMIntelFB's list at $REV"
else
  echo "STOP: iGPU id 0x$ID is not in NMIntelFB's list at $REV"; exit 1
fi

cd "$HOME" && REV=$REV bash "$HOME/nmx-intel/tools/intelfb/build.sh" 2>&1 | tee "$HOME/nmx-intel-build.log" | grep -E '^(patch:|NMIntelFB |could not)' 
echo "patches applied: $(grep -c '^patch:' "$HOME/nmx-intel-build.log") (the reference build applied 21)"
echo "kext: $HOME/nmx-build/intelfb/out/NMIntelFB.kext"
plutil -p "$HOME/nmx-build/intelfb/out/NMIntelFB.kext/Contents/Info.plist" | grep -E 'CFBundleIdentifier|IOPCIMatch|IOProviderClass'
