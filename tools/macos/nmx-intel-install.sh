#!/bin/bash
# Installs the NMIntelFB built by nmx-intel-build.sh, the 45 s start delay, the boot job and disables sleep.
# Run as root:  sudo bash nmx-intel-install.sh     (read it first; it runs three scripts from the nmx-intel repo as root)
# Prerequisite: NullMoth driver 2.3.6 installed and the RTX showing "Metal Support: Metal 3" (see docs/HYBRID-NMINTELFB.md).
set -uo pipefail
[ "$EUID" -eq 0 ] || { echo "Run with sudo."; exit 1; }
U=${SUDO_USER:-$(logname)}; H=$(eval echo "~$U"); LOG="$H/Desktop/nmx-intel-install.log"
{
  command -v kmutil >/dev/null || { echo "STOP: no kmutil"; exit 1; }
  kmutil showloaded --list-only | grep -qi com.nullmoth.NVAccel || { echo "STOP: NullMoth NVAccel is not loaded; install and verify the NVIDIA driver first"; exit 1; }
  grep -q 'nmxintel' <(nvram boot-args) && { echo "STOP: nmxintel is in boot-args, turn the AMD/Intel test driver off first"; exit 1; }
  echo "=== 1. NMIntelFB";  bash "$H/nmx-intel/tools/intelfb/install.sh"; r=$?; echo "exit $r"
  [ $r = 0 ] || { echo "STOP: install.sh failed, nothing else done"; exit 1; }
  echo "=== 2. 45 s delay"; nvram nullmoth-intelfb-delay=45; nvram nullmoth-intelfb-delay
  echo "=== 3. boot job";   bash "$H/nmx-intel/tools/intelfb/auto.sh" install; echo "exit $?"
  echo "=== 4. sleep off";  pmset -a disablesleep 1; pmset -g | grep -i sleepdisabled
  echo "=== check"
  ls -la /Library/Extensions | grep -iE 'NMIntelFB|NVRM|NVAccel'
  kmutil inspect -a x86_64 -A /Library/KernelCollections/AuxiliaryKernelExtensions.kc 2>/dev/null | grep -i nullmoth
  nvram boot-args; nvram -p | grep -i nullmoth
  echo "All five kexts must be in the auxiliary collection before you reboot. Then do a FULL shutdown and power on."
} 2>&1 | tee "$LOG"
