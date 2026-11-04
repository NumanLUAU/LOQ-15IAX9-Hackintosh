# Graphics analysis for my LOQ 15IAX9 (RTX 2050 + UHD 468B)

This is how I worked out which graphics setup to use on this laptop, what I tried, and what actually worked. Hardware facts come from my own machine (`diagnostics/hardware_inventory.md`). Project facts come from the READMEs and sources of the projects I cloned into `refs/`.

## What is actually in the laptop

| | Measured |
|---|---|
| iGPU | Intel UHD `8086:468B` rev 0C, subsys `17AA:3D06`, at 00:02.0 (Alder Lake-S/HX die) |
| dGPU | NVIDIA RTX 2050 Laptop `10DE:25ED` rev A1, subsys `17AA:3D06`, 01:00.0 under PEG1, 4 GiB, **GA107 = Ampere** (not Turing), BAR1 4096 MiB, VBIOS 94.07.8B.00.4E |
| Panel | 1920x1080 144 Hz, EDID `CSW 150F` |
| Hybrid mode | `dxdiag` in Windows: the Intel adapter reports `Output Type: Internal`, the NVIDIA adapter reports `HDMI`. The internal panel is wired to the iGPU and the HDMI port to the dGPU |
| MUX | The BIOS has a MUX switch (Graphics Device, dGPU only). The DSDT already hinted at it: the EC brightness queries `_Q11` and `_Q12` branch on `IGDS` to either `GFX0.DD1F` (iGPU panel) or `PEG1.PEGP.LCD0` (panel on the dGPU), and `LCD0` supplies the panel's EDID from ACPI. In dGPU-only mode the panel moves to the NVIDIA GPU and the iGPU disappears from the PCI bus |

## What I tried, and the result

| Setup | Result |
|---|---|
| Hybrid mode, NullMoth, firmware framebuffer for the panel | The HDMI monitor runs on the NVIDIA GPU with Metal. The internal panel is not recognized by the driver and only shows the boot text, then nothing. Mirroring showed only a cursor on the second display |
| **dGPU-only (MUX) mode, NullMoth, iGPU hidden** | **Works. The internal panel and the HDMI monitor both register on the NVIDIA GPU, with full Metal acceleration and brightness control. This is what I run on Sequoia and Tahoe** |
| Hybrid mode, WhateverXe on the iGPU plus NullMoth for the NVIDIA GPU | Both kexts loaded with no crashes, but the internal screen went blue and the boot stuck waiting for the HID driver. I removed WhateverXe |

## NullMoth (nvidia-macos-driver 2.7.1) vs the RTX 2050

1. **Device ID supported?** Yes. `25ED` is in `SUPPORTED_IDS` of the installer.
2. **Physically validated by NullMoth?** No. Their `docs/CARD-SUPPORT.md` (checked again for 2.7.1) lists Turing, Ampere and Ada as pending, and only Blackwell cards are validated. A list entry is not validation. I have validated it myself on this one laptop: it runs, with Metal, on both Sequoia and Tahoe.
3. **Architecture and firmware?** Ampere is covered by NVIDIA's open RM (Turing and newer) and the GSP firmware the driver ships.
4. **MUX?** NullMoth says accepting a PCI ID does not implement an Optimus display mux. It only drives outputs that are physically wired to the NVIDIA GPU. That is why I need the BIOS MUX switch in dGPU-only mode for the internal panel.
5. **Coexisting with WhateverXe?** Not documented upstream. I tried it (see above) and it hung, so it is not part of my setup.
6. **Limits:** sleep works for me on 2.7.1, but S3 (deep sleep) and hibernation do not, so I switch hibernation off with `pmset`. Older NullMoth versions could not wake the GPU after sleep (the PCIe link is cut and the screen stays black). The 2.7 docs describe system sleep and wake support, which they tested on a desktop RTX 5050 with macOS 15.8.1. Brightness needs the opt-in `nvrmacpibl=1`, which NullMoth warns hung some laptops. It works on mine.
   Audio on Tahoe: NullMoth 2.7 ships its own HD Audio driver for Tahoe (Apple removed AppleHDA). My EFI uses SimpleHDA instead, which works, so I have not tried NullMoth's.
7. **Install model:** the kexts install into `/Library/Extensions` and the auxiliary kernel collection from inside macOS, not into `EFI/OC/Kexts`. OpenCore only needs SIP `0x0A43`, the NullMoth boot-args, `SecureBootModel=Disabled`, Lilu and AMFIPass, and (panel on the dGPU) the `IONDRVSupport` block.

## WhateverXe vs the iGPU

* `468B` is in WhateverXe's device table (Alder Lake-S/HX), but its tested hardware is the desktop UHD 770 (HDMI, DP, USB-C) and Alder Lake-H laptop outputs. Internal eDP on ADL-S/HX is untested upstream.
* It needs Lilu, `WhateverXe.kext`, its own modified AMFIPass, SIP `0x803`, boot-args `-allow3d -disablegfxfirmware`, the `WhateverXe-Graphics` package installed in macOS and an `SSDT-PNLF`.
* WhateverGreen and WhateverXe must never be loaded together. WhateverGreen is not in my EFI.

## WhateverGreen

It is not an NVIDIA driver. It patches Intel and AMD graphics, DRM and board-id checks. I do not need it: the iGPU is disabled, and the NVIDIA GPU is NullMoth's job. `-wegnoegpu`, `agdpmod=pikera` and `nv_disable=1` must not be used with NullMoth.

## 1401 (the Windows builder and the Mac app)

1401 has two parts, and I use only one of them.

**The Windows app, which I did not use for my EFI.** It needs administrator rights, erases a USB stick, builds an EFI with OpCore-Simplify, picks the `iMacPro1,1` SMBIOS and writes the NullMoth settings. NullMoth describes it as tested end to end on only a small number of PCs. I tried that route first, but the EFI it generated kept running into ACPI table problems and kernel panics on this laptop, so I gave up on it and made my own EFI from scratch against my own ACPI tables. That also let me make the choices a generic builder cannot: the dual boot with a custom Windows entry, the GoldenGate theme, the Custom SMBIOS GUID so Windows keeps its Lenovo identity, and the fixes for this specific laptop (see the README).

**The Mac app (`1401-Mac-*.dmg`), which I do use.** Once macOS boots from my own EFI, the Mac app installs and updates the NullMoth driver. It also helps in a few other ways:
* It adds the "1401: Remove NVIDIA driver" and "1401: Start once without NVIDIA driver" picker entries, which are my recovery path from a bad driver install. I keep those entries disabled in `config.plist` until I need them.
* It edits the OpenCore config and writes backups next to it (`config.plist.nullmoth-*`). It added `nvfbhidpi=1`, `nvrmacpibl=1` and, on Tahoe, `revpatch=sbvmm`.
* It generated the USB map (`UTBMap.kext` with `USBToolBox.kext`) from the running system.

The app edits the config on the volume OpenCore booted from, so keep that stick or partition attached while it runs. I copy its changes back into my EFI afterwards so the files in this repo match what boots.

## Decision

My setup is dGPU-only (MUX) mode with the iGPU hidden: the NVIDIA RTX 2050 drives both the internal panel and the HDMI monitor with full Metal acceleration, on Sequoia and on Tahoe. Hybrid mode only works for external monitors on the NVIDIA ports, and the one iGPU route I tried (WhateverXe) failed for me.
