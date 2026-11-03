# Graphics analysis - LOQ 15IAX9 (RTX 2050 + UHD 468B)

All hardware facts are from this machine (`diagnostics/hardware_inventory.md`); project facts are from the cloned READMEs/sources in `refs/` (read 2026-11-03).

## What is actually in the laptop

| | Measured |
|---|---|
| iGPU | Intel UHD `8086:468B` rev 0C, subsys `17AA:3D06`, at 00:02.0 (Alder Lake-S/HX die) |
| dGPU | NVIDIA RTX 2050 Laptop `10DE:25ED` rev A1, subsys `17AA:3D06`, 01:00.0 under PEG1, 4 GiB, **GA107 = Ampere** (not Turing), BAR1 4096 MiB, VBIOS 94.07.8B.00.4E |
| Panel | 1920x1080 144 Hz, EDID `CSW 150F` |
| Routing right now | `dxdiag`: **Intel** reports `Output Type: Internal`; **NVIDIA** reports `HDMI` (the external VA24G1-H). Hybrid/Optimus style -> the panel is on the iGPU, the HDMI port is on the dGPU. |
| MUX | Not readable from Windows. DSDT evidence: EC brightness queries `_Q11/_Q12` branch on `IGDS` -> `GFX0.DD1F` (iGPU panel) **or** `PEG1.PEGP.LCD0` (panel on dGPU). So firmware has a dGPU-panel mode; whether the BIOS exposes the switch must be checked by you. The related reference README (`pranish-dev/loq_hackintosh`, 15IRX9/15IAX9 family) says BIOS has *Graphics Device: Discrete*. |

## NullMoth (nvidia-macos-driver 2.6.6) vs the RTX 2050

1. **Device ID supported?** Yes - `25ED` is in `SUPPORTED_IDS` (`package/install.sh`).
2. **Physically validated?** No. `docs/CARD-SUPPORT.md`: Turing/Ampere/Ada rows say *"Pending"*; only Blackwell RTX 5060 (automated) and 5070/5080 (reported) are validated; 4050 laptop appears in their test notes and in the reference EFI. A list entry != validation, and there is **no RTX 2050 report**.
3. **Architecture/firmware?** Ampere is within NVIDIA's open-RM (Turing+) and GSP firmware 615.78.08. Turing gets extra start-up settle time; Ampere doesn't need it.
4. **MUX?** NullMoth: *"accepting its PCI ID does not implement an Optimus display mux"* - it only drives outputs physically wired to the NVIDIA GPU. Panel only in dGPU-only mode (profile B); HDMI in Hybrid (profile C).
5. **Coexist with WhateverXe?** Not documented. NullMoth documents coexistence with *WhateverGreen* (add `gfxrst=4`). WhateverXe is a WhateverGreen derivative, so profile E reuses `gfxrst=4`, but this pairing is an untested guess.
6. **Limits:** sleep (PCIe link cut -> GOP not re-inited -> black screen, workaround `pmset disablesleep`), brightness (`nvrmacpibl=1` opt-in; NullMoth says it hung some laptops), outputs limited to the dGPU's.
7. **Install model:** kexts install into `/Library/Extensions` + AuxKC - **not** `EFI/OC/Kexts`. OpenCore only needs SIP `0x0A43` (`csr-active-config 430A0000`), the boot-args, `SecureBootModel=Disabled`, Lilu + AMFIPass, and (panel on dGPU) `IONDRVSupport` block. Installer rule: use `ResizeAppleGpuBars=0`, `ResizeGpuBars=-1` while installing.

## WhateverXe (0.7.0) vs the iGPU

* `468B` is in `docs/device-selection.md` (Alder Lake-S/HX). Tested hardware: Alder Lake-S **UHD 770 desktop (HDMI/DP/USB-C)**; Alder Lake-H laptop outputs. **Internal eDP on ADL-S/HX is not tested**; README lists internal eDP as implemented for ADL-P/U/H only. So acceleration may work but the **panel may stay black or unaccelerated** - profile D is a genuine experiment.
* Needs: Lilu, `WhateverXe.kext`, Mod-AMFIPass, `csr-active-config 03080000`, boot-args `-allow3d -disablegfxfirmware`, `WhateverXe-Graphics-0.4.0.pkg` installed in macOS, `SSDT-PNLF` (included for D/E), DVMT 96 MB.
* WhateverGreen and WhateverXe are **never** loaded together; WhateverGreen is not in this EFI at all.

## WhateverGreen

Not an NVIDIA driver (patches Intel/AMD, DRM, board-id). Not needed: WEX covers the Intel iGPU; NVIDIA is NullMoth's job. `-wegnoegpu`/`agdpmod=pikera`/`nv_disable=1` must not be used with NullMoth.

## 1401 (official Windows builder)

Windows app (needs admin, erases a USB stick, uses OpCore-Simplify, chooses `iMacPro1,1`, writes the NullMoth bits). It is self-described as tested end-to-end on "a small number of PCs". I did **not** run it: it requires elevation and a USB write, and it can't make the dual-boot/GoldenGate/Custom-SMBIOS choices you asked for. Useful as a cross-check after you boot; its Mac app (`1401-Mac-*.dmg`) is the supported way to install/uninstall the NullMoth driver and adds a *"Remove NVIDIA driver"* picker entry for recovery from a bad driver.

## Decision

Deliverable priority "iGPU+NVIDIA -> NVIDIA -> iGPU" = profiles **E -> B/C -> D**, but since none are validated for this exact machine, the delivered default (A) is the profile that is guaranteed to bring up a framebuffer for the installer.
