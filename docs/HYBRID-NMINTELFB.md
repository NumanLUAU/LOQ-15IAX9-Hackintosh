# Hybrid mode with NMIntelFB: RTX 2050 renders, Intel iGPU only scans out

This is the route for keeping the BIOS in Hybrid mode (no MUX change). The NVIDIA RTX 2050 does all the rendering with NullMoth's driver, and NMIntelFB (NullMoth's framebuffer kext with the nmx-intel patches) sends each finished frame to the internal panel through the Intel display engine. I adapted it from the write-up of a working Tiger Lake install (ASUS TUF Dash F15, RTX 3060, iGPU 8086:9A49) and from the nmx-intel project (kitsuneislife/nmx-intel). I have not run it on my machine yet.

## What I checked from the sources

| Check | Result |
|---|---|
| My iGPU 8086:468B in NMIntelFB's accepted list at NullMoth v2.3.6 | Yes, `{0x468b, 12}` (display version 12) |
| My RTX 2050 (10DE:25ED) in the NullMoth 2.3.6 installer's device table | Yes |
| My BIOS is in Hybrid mode right now (Windows shows the panel on the Intel adapter, HDMI on NVIDIA) | Yes, no BIOS change needed |
| nmx-intel patch set present | Yes, 21 NMIntelFB patches in `tools/intelfb/` |

Not verified: it has only been run on a Tiger Lake iGPU (9A49) and, upstream, on a Raptor Lake one (A7A8). My iGPU is Alder Lake-S/HX (468B) with a different panel path, and the RTX 2050 has not been validated by NullMoth on any version.

## Differences from the guide for my machine

| Topic | Guide's machine | Mine |
|---|---|---|
| iGPU | 8086:9A49 | 8086:468B |
| dGPU | RTX 3060 (10DE:2520) | RTX 2050 Laptop (10DE:25ED, GA107) |
| OpenCore config | WhateverGreen on, nothing on the iGPU | No WhateverGreen. `profiles/Sequoia/config-hybrid-NMIntelFB.plist` leaves the iGPU alone |
| What must NOT be in the config | iGPU DeviceProperties, IONDRVSupport block | My dGPU-only profile has both (`class-code` hide on `Pci(0x2,0x0)` and the IONDRVSupport block). The hybrid profile removes them |
| NullMoth version | 2.3.6 | I am on 2.6.6, so I have to go back to 2.3.6 (newer versions make the panel blink with this route) |
| Extra boot-args | `-igfxvesa gfxrst=4` (WhateverGreen) | Not needed, no WhateverGreen. I also dropped `nvfbhidpi` and `nvrmacpibl` (added by the 2.6.x app, not for this route) |

## Steps

1. **Remove NullMoth 2.6.6** while I am still on the working dGPU-only setup: 1401 app, Remove the driver (or the picker entry "1401: Remove NVIDIA driver"). Keep a copy of the current USB config.
2. **Switch the stick to the hybrid profile** (from Windows): copy `EFI-private-Sequoia\profiles\config-hybrid-NMIntelFB.plist` over `EFI\OC\config.plist` on the stick, keeping the old file as a backup. Leave the BIOS in Hybrid. Put these on the stick too: `dl\NullMoth-2.3.6\1401-Mac-2.3.6.dmg` (checksum verified against the release) and the two scripts in `tools\macos\`.
3. **Install NullMoth 2.3.6** in macOS: open `1401-Mac-2.3.6.dmg`, replace `/Applications/1401.app`, confirm the version (`plutil -p /Applications/1401.app/Contents/Info.plist | grep ShortVersion` says 2.3.6), run its four steps. Read the log before rebooting: it must say `the built-in screen runs on the Intel GPU through the firmware framebuffer; IONDRVSupport stays on`. If it says it blocks IONDRVSupport, do not reboot; disable that `Kernel > Block` entry first. Never press "Check for a newer driver" afterwards.
4. **Verify the RTX is a headless Metal device** after the reboot (the screen still looks unaccelerated, that is expected):
```bash
kmutil showloaded --list-only | grep -i nullmoth        # four modules, version 2.3.6
system_profiler SPDisplaysDataType | grep -E 'Chipset|Metal'   # RTX 2050, Metal 3
nvram -p | grep nullmoth                                  # nullmoth-nv-ok 1
```
   If the guard trips (a `nullmoth-nv-starts` counter), run `sudo nvram -d nullmoth-nv-starts` and reboot. Do not go on until the RTX shows Metal 3.
5. **Build NMIntelFB** (no root, installs nothing): install the Command Line Tools (`xcode-select --install`), then
```bash
bash tools/macos/nmx-intel-build.sh
```
   It clones nmx-intel and NullMoth's repo, checks my iGPU id is accepted at v2.3.6, applies the patches and builds. The reference build printed `NMIntelFB 241aff3d 120592 B (v2.3.6)`; mine may differ.
6. **Install it** (read the script first, it runs three nmx-intel scripts as root):
```bash
sudo bash tools/macos/nmx-intel-install.sh
```
   It installs the kext, sets `nullmoth-intelfb-delay=45`, installs the boot job and turns sleep off. All five kexts must be in the auxiliary collection before rebooting.
7. **Full shutdown**, wait ten seconds, power on. The logo stays about 45 seconds longer. Expect the screen to blink or go black for a few seconds while the RTX takes over.
8. **Verify**:
```bash
sysctl debug.nvaccel_iop debug.nvaccel_iop_ok debug.nvaccel_iop_fail debug.nmintelfb_agdc
# iop 1, iop_ok growing, iop_fail 0, agdc 1
nvram nullmoth-intelfb-trail        # must end with "alive"
system_profiler SPDisplaysDataType | grep -E 'Chipset|Metal|Looks like'
```

## If it goes wrong

* Black screen: wait three minutes, then force power off and boot again. If the NMIntelFB start never returned it skips itself next boot and I get the unaccelerated desktop back (`sudo nvram -d nullmoth-intelfb-attaching` to let it try again).
* Turn it off without removing it: add `-nmintelfboff` to boot-args, or `sudo nvram nullmoth-intelfb=0`.
* Boot the picker entry "1401: Start once without NVIDIA driver", or boot from a stick with a known-good EFI. Kexts in `/Library/Extensions` load whatever EFI is used, so a kext that hangs boot has to be removed from Recovery (move `NMIntelFB.kext` and `AuxiliaryKernelExtensions.kc` out of `/Library`).
* Uninstall: `sudo bash ~/nmx-intel/tools/intelfb/auto.sh remove`, `sudo bash ~/nmx-intel/tools/intelfb/install.sh remove`, `sudo nvram -d nullmoth-intelfb-delay`, `sudo pmset -a disablesleep 0`, reboot.
* Back to the dGPU-only setup: restore the old `config.plist` on the stick, set the BIOS to Discrete, and reinstall the newer NullMoth if I want it.

## Limits (from the original write-up)

One display only (the internal panel at its native mode), no sleep, about 45 seconds extra per boot, stuck on NullMoth 2.3.6, the RTX stays powered, and external ports on the RTX were not tested together with NMIntelFB. I will not install macOS updates without a plan.

## Credits

NullMoth (driver, 1401 and NMIntelFB source), kitsuneislife (nmx-intel patches and boot job, and the original write-up this is adapted from).
