# Lenovo LOQ 15IAX9 (83GS) Hackintosh, macOS Tahoe 26.x and Sequoia 15.x, OpenCore 1.0.8

This is the OpenCore EFI I built for my Lenovo LOQ 15IAX9 (Intel Core i5-12450HX, NVIDIA GeForce RTX 2050 Laptop). macOS runs with full Metal acceleration on the RTX 2050 through the NullMoth driver. The internal panel and the HDMI port are both driven by the NVIDIA GPU, and the Intel iGPU is switched off.

There are two EFIs, one per macOS version:

| Folder | macOS | Notes |
|---|---|---|
| `EFI-Tahoe/` | Tahoe 26.x | The one I run now. Everything works except sleep |
| `EFI-Sequoia/` | Sequoia 15.x | The EFI I used before I updated to Tahoe, kept as it was |

It is based on pranish-dev/loq_hackintosh (same laptop family, RTX 4050). I did not copy it. I read it, rebuilt everything against my own machine's ACPI tables and hardware IDs, and fixed the things that broke on mine. This README lists what I changed compared with a regular OpenCore `config.plist`, in two parts: what any Alder Lake CPU needs, and what this specific laptop needs. A separate section lists what differs between Sequoia and Tahoe.

Everything below was measured on my machine. The hardware inventory and the original ACPI tables are in my local `diagnostics/` folder, which is not part of the repo.

## Hardware

| Part | Detail |
|---|---|
| Model | Lenovo LOQ 15IAX9, machine type 83GS, board LNVNB161216, BIOS NECN43WW (2025-02-24) |
| CPU | Intel Core i5-12450HX, 4 P-cores + 4 E-cores, CPUID 0x90672, Hyper-Threading off (8 threads) |
| GPU (used) | NVIDIA GeForce RTX 2050 Laptop, GA107 (Ampere), PCI 10DE:25ED, 4 GiB |
| GPU (disabled) | Intel UHD Graphics, PCI 8086:468B |
| RAM | 12 GiB DDR5-4800, single channel |
| Display | 15.6 inch 1920x1080 144 Hz (EDID manufacturer CSW) |
| Audio | Realtek ALC257 (layout 99) |
| Ethernet | Realtek RTL8168 rev 15 (10EC:8168) |
| Wi-Fi / Bluetooth | Intel AX203 (CNVi, 8086:7AF0) / Intel USB Bluetooth 8087:0026 |
| Touchpad | Goodix GXTP5100, I2C HID on controller 8086:7ACC |
| Keyboard | PS/2 (ACPI MSFT0001 with compatible ID PNP0303) |
| SSDs | WD PC SN5000S (Windows), Intel 660p (macOS volume and data) |

## What works on my machine

| Feature | Tahoe 26.x | Sequoia 15.x |
|---|---|---|
| Boot to macOS through OpenCore | Works | Works |
| NVIDIA Metal acceleration (NullMoth) | Works | Works |
| Internal panel on the NVIDIA GPU | Works in BIOS dGPU-only mode (this laptop has a MUX switch). In Hybrid mode the panel is not recognized | Same |
| Internal panel and HDMI together (dual display) | Works in dGPU-only mode, both register on the NVIDIA GPU | Same |
| Brightness control | Works (`nvrmacpibl=1`) | Works |
| Keyboard, mouse, USB ports, Thunderbolt/USB-C | Works | Works |
| Audio output and microphone | Works (needs SimpleHDA, see below) | Works (AppleALC alone) |
| Wi-Fi (native menu, no HeliPort) | Works (laobamac Tahoe build) | Works (pranish-dev 2.4.0 build) |
| Bluetooth | Works (`-ibtcompatbeta` and two NVRAM keys) | Works (two NVRAM keys) |
| Touchpad | Works (VoodooI2C match fix) | Works |
| Android USB tethering (HoRNDIS) | Works | Works |
| macOS updates (OTA) | iBridged included | Not needed |
| Sleep and hibernation | Not supported by the NullMoth driver, switch them off | Same |
| Intel iGPU | Disabled on purpose | Disabled on purpose |

The Sequoia column is how it behaved before I updated to Tahoe. I have not re-tested Sequoia since.

## BIOS settings (F2)

| Setting | Value | Why |
|---|---|---|
| Graphics Device (MUX) | Discrete / dGPU only | Routes the internal panel to the NVIDIA GPU. Without this the panel stays on the Intel iGPU, which macOS cannot drive. Windows then also runs on the RTX 2050 only |
| Hyper-Threading | Disabled | Alder Lake with HT panics the XNU scheduler (cpu_thread_alloc). Cost in Windows: 4 fewer threads |
| Secure Boot | Disabled | |
| Fast Boot, CSM | Disabled | UEFI only |
| Above 4G Decoding / Resizable BAR | Enabled | The RTX 2050 exposes a 4 GiB BAR |
| VT-d | Disabled or enabled | `DisableIoMapper` covers either |
| Storage mode | AHCI / NVMe, never RST, VMD or RAID | |

Windows Fast Startup was on when I inspected the machine. It is fine, but turn it off if the Windows partition ever looks inconsistent after dual booting. Do a full shutdown (not a restart) when going from Windows to macOS: the Wi-Fi/Bluetooth module is shared and Windows can leave it in a state macOS cannot use.

## Part 1: what I changed from a regular config.plist to run an Alder Lake CPU

Apple never shipped macOS on Alder Lake or on hybrid P/E-core CPUs. These are the changes that make the kernel boot. They are the same in both EFIs.

| Section | Key | Value | Why |
|---|---|---|---|
| Kernel > Emulate | Cpuid1Data | 55 06 0A 00 then zeros | Presents the CPU as Comet Lake (CPUID 0x0A0655) so XNU picks a supported CPU family |
| Kernel > Emulate | Cpuid1Mask | FF FF FF FF then zeros | Only the signature word is replaced |
| Kernel > Quirks | ProvideCurrentCpuInfo | true | Gives XNU the real topology and TSC/FSB values instead of trusting the spoof (8 cores, 8 threads, 2688 MHz) |
| Kernel > Quirks | AppleXcpmCfgLock | true | CFG Lock is on (log: EIST CFG Lock 1) and Lenovo hides the option, so the MSR write is patched instead |
| Kernel > Quirks | DisableIoMapper | true | The firmware ships a DMAR table (VT-d); this avoids broken DMA mappings without deleting the table |
| Kernel > Quirks | DisableLinkeditJettison | true | Keeps symbols available for kext patching and readable panics |
| Kernel > Quirks | PanicNoKextDump, PowerTimeoutKernelPanic | true | Cleaner panics, no power-state timeout panics |
| Kernel > Quirks | XhciPortLimit | false | The 15-port limit is solved properly with a USB map instead (see USB below) |
| Booter > MmioWhitelist | 0xFF000000 | enabled | **I found this by debugging.** With DevirtualiseMmio on, the kernel page-faults at 0xFF04504C (firmware flash region) about one second after boot. Whitelisting the region fixes it |
| Booter > Quirks | DevirtualiseMmio, RebuildAppleMemoryMap, SyncRuntimePermissions, SetupVirtualMap, ProtectUefiServices, ProvideCustomSlide, EnableSafeModeSlide, AvoidRuntimeDefrag, AllowRelocationBlock, FixupAppleEfiImages | true | The standard set for 12th gen firmware with a UEFI 2.8 memory attributes table. EnableWriteUnprotector stays false |
| Booter > Quirks | ResizeAppleGpuBars | -1 | Leave GPU BAR sizing to the firmware and driver (see NVIDIA below) |
| UEFI > Quirks | ResizeGpuBars | -1 | Same reason |
| ACPI | SSDT-PLUG | 16 Processor() objects, plugin-type 1 on the first | The DSDT only has Device(PRxx) CPU objects, which AppleACPICPU ignores. Without Processor() objects XCPM never loads and boot stalls after AppleCredentialManager |
| Kexts | CpuTscSync | enabled | Keeps the TSC synchronised across the hybrid cores |
| Kexts | RestrictEvents | enabled, revcpu=1, revcpuname set, revpatch=cpuname | About This Mac shows the real name "12th Gen Intel Core i5-12450HX" instead of the spoofed Comet Lake |
| Misc > Security | SecureBootModel | Disabled | Required for the NullMoth driver |
| PlatformInfo | SystemProductName | MacBookPro16,2 | Laptop model supported by Sequoia and Tahoe (battery, lid, backlight behaviour) with no AMD dGPU switching logic |

Two things that are easy to get wrong on this CPU family:
* Hyper-Threading must stay off. The BIOS setting is the fix. I found no OpenCore setting that replaces it.
* Do not add CpuTopologyRebuild. pranish-dev removed it because it breaks the PS/2 keyboard interrupt on Lenovo laptops.

## Part 2: what I changed to make THIS laptop work

### ACPI (generated from my DSDT, sources in `acpi_src/` and `source/acpi/`)

| File or patch | What it does and why |
|---|---|
| ACPI patch: DSDT HS06 scope | **I found this by debugging.** macOS's old ACPI interpreter aborts the whole DSDT load at `Scope(_SB.PC00.XHCI.RHUB.HS06)` because HS06 only exists when a firmware variable is large enough. The screen showed "DSDT table load failed", and there was no EC and no keyboard. The patch turns that scope into `If (One)` plus Noops (same length). It is a runtime patch, not a replacement DSDT, so the firmware's live NVS addresses stay correct. It matches exactly once in my DSDT |
| ACPI patch: `_OSI` to `XOSI` | Lets macOS answer as a recent Windows. The DSDT gates I2C, thermal and power code on OSYS >= 0x07DF |
| SSDT-XOSI | Defines XOSI: true for Windows 2001 through Windows 2022 under Darwin, passes through to the real `_OSI` otherwise |
| ACPI patch: `GPRW` to `XPRW` and SSDT-GPRW | Stops instant wake from the XHCI/XDCI wake source (GPRW(0x6D,4)) |
| SSDT-EC-USBX | Adds a fake EC (ACID0001) under `\_SB.PC00.LPCB` so macOS finds an "EC" device. The real EC (EC0, PNP0C09) stays active for battery and Fn keys. Also adds USB sleep/wake power properties |
| SSDT-RTCAWAC | Sets STAS to 1 under Darwin so the legacy RTC is used instead of the AWAC clock macOS cannot drive |
| SSDT-PLUG | See Part 1 |

All tables are gated on `_OSI("Darwin")` and the renames forward to the originals, so Windows sees stock behaviour. I do not use a replacement DSDT and I did not copy any AML from the reference EFI.

### Kexts

Most kexts are the same in both EFIs. The rows marked Tahoe or Sequoia differ.

| Kext | Version | Purpose on this laptop |
|---|---|---|
| Lilu | 1.7.2 | Patch engine |
| VirtualSMC, SMCBatteryManager | 1.3.8 | SMC and battery (EC0 fields, BAT1) |
| AppleALC | 1.9.8 | ALC257, layout-id 99 injected on `Pci(0x1f,0x3)` |
| SimpleHDA (Tahoe only) | 1.0.0 | laobamac's Lilu plugin that restores AppleHDA on Tahoe (Apple removed it). Must load after AppleALC and needs `keepsyms=1`. I tried to use VoodooHDA first, but it has to be built and installed on the Mac itself and sounds worse, so I went with SimpleHDA. The optional `SimpleHDA-HAL` package is not needed for me |
| NVMeFix | 1.1.3 | NVMe power management |
| RestrictEvents | 1.1.6 | CPU name (`revcpu`, `revcpuname`, `revpatch=cpuname`). Tahoe uses the RELEASE build and also `revpatch=sbvmm` |
| iBridged (Tahoe only) | 1.0.1 (RELEASE) | Lilu plugin by Carnations-Botanica that fixes macOS OTA updates (patches BridgeOSInstall). Needed for updating to Tahoe |
| CpuTscSync | 1.1.2 | TSC sync |
| BrightnessKeys | 1.0.3 | Fn brightness keys |
| VoodooPS2Controller (keyboard plugin only) | 2.3.7 | PS/2 keyboard. I removed the Mouse and Trackpad plugins (no PS/2 pointing device) |
| VoodooI2C + VoodooI2CHID | 2.9.1 | I2C touchpad. **Modified Info.plist only:** official 2.9.1 does not match the Alder Lake-S I2C controller 8086:7ACC, so I added `0x7acc8086&0xFFFCFFFF` to the `VoodooI2CPCILakeController` match list. The binary is untouched. It runs in polling mode (`-vi2c-force-polling` and `force-polling` on `Pci(0x15,0x0)`) because GPIO/APIC interrupts do not work |
| RealtekRTL8111 | 3.0.0 | RTL8168 ethernet |
| AirportItlwm (Tahoe) | 2.4.0 alpha | Native Wi-Fi for the AX203. **Third-party build** from laobamac/itlwm (v2.4.0-alpha, Tahoe RELEASE, commit 7204c69), no root patches needed, limited to Darwin 25.x. Before this I tried AirportItlwm-Tahoe 1.0.0 by kgp-macPro: it needs OCLP-CustoMac root patches and my Wi-Fi was broken with it. Fallback if native Wi-Fi ever breaks: official `itlwm.kext` 2.3.0 plus the HeliPort app |
| AirportItlwm (Sequoia) | 2.4.0 | **Third-party build** from the pranish-dev/loq_hackintosh EFI. The official 2.3.0 Sonoma 14.4 build fails vtable patching on Sequoia (seen in the OpenCore log). Limited to Darwin 24.x |
| IntelBluetoothFirmware, IntelBTPatcher | 2.5.0 | Intel BT 8087:0026. **Third-party builds** from the pranish-dev/loq_hackintosh EFI (newer than the official 2.4.0 release, which did not work for me) |
| BlueToolFixup | 2.7.3 | Monterey and later Intel Bluetooth (reference EFI build, newer than the official 2.7.2). On Tahoe the boot argument `-ibtcompatbeta` is also needed |
| HoRNDIS | 9.2 | Android USB tethering (last official release, unmaintained) |
| AMFIPass | 1.4.1 | Lets WindowServer load the NullMoth bundle |
| USBToolBox + UTBMap | | USB map generated by the 1401 Mac app for this laptop (see USB) |

Not included on purpose: WhateverGreen and WhateverXe (the iGPU is disabled), SMCProcessor and SMCLightSensor, YogaSMC and LOQFanMon (unverified third-party binaries).

### USB

The DSDT declares 14 high-speed and 10 super-speed ports, which is more than macOS's 15-port limit. The 1401 Mac app generated a USB map (`UTBMap.kext`, with `USBToolBox.kext`) from the running system. It contains HS02 (USB-C), HS03 and HS04 (external ports), HS09, HS08 (internal ITE controller) and HS14 (internal Bluetooth, connector type 255). The built-in camera is on Windows port 6 and is not in this map. Add it if you need the camera. This map belongs to my machine, so make your own.

### NVIDIA (NullMoth) specifics

NullMoth installs into `/Library/Extensions` and the auxiliary kernel collection after macOS is installed (the 1401 Mac app does it and updates it). It does not go in `EFI/OC/Kexts`. OpenCore only sets the following:

| Where | Value | Why |
|---|---|---|
| boot-args | `nvfb=1 nvaccel=1 nvfbheads=4 -nvkmsnosmooth` | Framebuffer, accelerator, up to 4 display heads, smooth scanout |
| boot-args | `amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0` | Lets WindowServer load the unsigned Metal bundle |
| boot-args | `nvfbhidpi=1` | HiDPI "looks like" modes (added by the 1401 app) |
| boot-args | `nvrmacpibl=1` | Bridges the brightness slider to the dGPU panel's ACPI backlight method (added by the 1401 app; NullMoth warns it hung some laptops, it works here) |
| NVRAM | `csr-active-config` 43 0A 00 00 (0x0A43) | Unsigned kexts plus root patches |
| Kernel > Block | `com.apple.iokit.IONDRVSupport`, Exclude | Stops Apple's firmware framebuffer from taking display index 0 |
| Misc > Tools | NullMothSafe.efi (two entries, disabled) | The 1401 "remove driver" tools. Enable them in `config.plist` if you ever need to recover from a bad driver install |

The RTX 2050 (25ED) is in NullMoth's device table, but their validation list does not include Ampere laptops, so this is a setup that works for me, not a vendor-validated one.

### Other laptop-specific settings

| Setting | Value | Why |
|---|---|---|
| UpdateSMBIOSMode + CustomSMBIOSGuid | Custom + true | The Mac identity is written to a private GUID so Windows, launched through OpenCore, should keep the real Lenovo SMBIOS. Not verified yet: after booting Windows from OpenCore, check that `Get-CimInstance Win32_ComputerSystem` says LENOVO / 83GS |
| Misc > Entries | Windows, path `PciRoot(0x0)/Pci(0x6,0x0)/Pci(0x0,0x0)/NVMe(0x1,CF-97-BB-40-8B-44-1B-00)/HD(1,GPT,0F149AA1-6499-4184-9827-7AAFD79B98E6,0x800,0x82000)/\EFI\Microsoft\Boot\bootmgfw.efi` | The real Windows ESP on my disk 0 (WD SN5000S), measured from the partition table. **You must replace this with the path of your own Windows ESP** |
| Misc > Security > ScanPolicy | 0x280103 | APFS only on NVMe and USB. The Windows ESP and the FAT32 stick are not auto-listed, so only the macOS volume and my custom Windows entry appear |
| Misc > Boot | HideAuxiliary true, Timeout 0 | Main list: Windows, macOS. Space shows Reset NVRAM. Timeout 0 waits forever |
| Drivers | HfsPlus, OpenRuntime, OpenCanopy, ResetNvramEntry (`--preserve-boot`) | Reset NVRAM entry that keeps the firmware's Windows Boot Manager option. Lenovo firmware can misbehave after NVRAM resets (OpenCore bug 995) |
| Theme | GoldenGate, plus Apple15.icns and Apple.icns and Windows11.icns (renamed Windows.icns) from the chris1111 Flavours-AppleSet theme | GoldenGate has no Apple logo and its Windows icon is a Boot Camp style disk. The three icons come from the same set so the macOS and Windows entries match |
| DeviceProperties | `Pci(0x2,0x0)` class-code FFFFFFFF | Hides the Intel iGPU from macOS (see below) |
| DeviceProperties | `Pci(0x1f,0x3)` layout-id 99; `Pci(0x15,0x0)` force-polling | Audio and touchpad |
| NVRAM | `bluetoothExternalDongleFailed` = 00 and `bluetoothInternalControllerInfo` = 14 zero bytes, both also in NVRAM > Delete | For Intel Bluetooth on Monterey and later: without them macOS remembers a failed controller and switches Bluetooth off a few seconds after it is enabled. Rewritten at every boot. Same keys the pranish-dev EFI uses. This fixed my Bluetooth |

## Sequoia versus Tahoe: what differs

Changes I made when I moved from Sequoia to Tahoe:

| Item | Sequoia EFI | Tahoe EFI |
|---|---|---|
| Wi-Fi kext | AirportItlwm 2.4.0 (pranish-dev build), Darwin 24.x only | AirportItlwm 2.4.0 alpha (laobamac Tahoe build), Darwin 25.x only |
| Audio | AppleALC only (macOS still has AppleHDA) | AppleALC then SimpleHDA 1.0.0 (Tahoe has no AppleHDA), plus `keepsyms=1` |
| Bluetooth | NVRAM keys | NVRAM keys plus boot argument `-ibtcompatbeta` |
| OTA updates | not needed | iBridged 1.0.1 |
| RestrictEvents | 1.1.6 | 1.1.6 RELEASE, plus `revpatch=sbvmm` in boot-args |
| boot-args extras | none | `-ibtcompatbeta`, `revpatch=sbvmm`, `keepsyms=1` |

Everything else (ACPI, Alder Lake settings, NullMoth arguments, USB map, picker) is identical.

Two Tahoe lessons that cost me time:
* The Wi-Fi kext matters. Tahoe has no usable legacy Wi-Fi stack for Intel cards, and the AirportItlwm-Tahoe 1.0.0 build I tried first needs OCLP-CustoMac root patches. The laobamac Tahoe build works without root patches. Keep the Sequoia kext restricted to Darwin 24.x and the Tahoe kext to Darwin 25.x if both systems share one config.
* Tahoe removed AppleHDA. Without SimpleHDA there is no audio even with AppleALC.

## Both displays on the NVIDIA GPU, iGPU disabled

How it works:
1. In BIOS set the graphics device to Discrete / dGPU only. This is the only thing that moves the internal panel to the NVIDIA GPU. In that mode the Intel iGPU is removed from the PCI bus, so macOS does not see it at all.
2. As a second layer, `config.plist` sets `class-code = FFFFFFFF` on the iGPU's PCI path so macOS ignores it even if it shows up. In dGPU-only mode this does nothing.
3. There is no boot argument that disables an Intel iGPU without WhateverGreen (`-wegnoigpu`). I left WhateverGreen out on purpose. If you add it, NullMoth requires `gfxrst=4`.

Warning: if the BIOS is left in Hybrid mode with this config, the internal panel is wired to the iGPU, which is now hidden and has no driver. You get kernel text and then a dead internal screen while HDMI keeps working.

Setting up two displays:
1. Boot macOS with the HDMI monitor connected (hot-plugging can leave it black).
2. System Settings, Displays. Both the internal panel and the HDMI monitor are listed under the NVIDIA GPU.
3. Drag the display rectangles to arrange them, or use a display's menu to mirror one to the other. The internal panel is 1920x1080 at 144 Hz. Use "Show all resolutions" or the HiDPI "looks like" list (enabled by `nvfbhidpi=1`).
4. Check with `system_profiler SPDisplaysDataType`: one GPU, two displays, Metal supported.
5. If the second display stays black, replug it, reboot with it connected, and check `kmutil showloaded --list-only | grep -i nullmoth` (should list 4 modules) and the log from the 1401 app.

## Repository layout and zips

| Path | Contents |
|---|---|
| `EFI-Tahoe/` | The EFI that boots Tahoe on my machine, with the SMBIOS values in `OC/config.plist` blanked out. Fill in your own before using it |
| `EFI-Sequoia/` | The EFI that booted Sequoia, same blanking |
| `profiles/Tahoe/`, `profiles/Sequoia/` | Config variants (SMBIOS blanked) for each OS: the shipped quiet NVIDIA-only profile, a quiet profile with a 5 second autoboot, and a verbose debug profile with all logging on. `profiles/Sequoia/` also has `config-hybrid-NMIntelFB.plist` for the hybrid route below |
| `acpi_src/`, `acpi_out/`, `source/` | ASL sources of the custom SSDTs and the compiled AML |
| `tools/` | iasl and the helper scripts I used (`macos/` has the NMIntelFB build and install scripts). `sync_private.py` mirrors each public EFI into my private copy and puts my real SMBIOS into its config |
| `refs/` | The reference projects I read while building this |
| `docs/` | ACPI analysis, graphics analysis, troubleshooting, hybrid mode with NMIntelFB, a write-up for forum posts |
| `experimental/` | Earlier generated profiles and the one-off scripts used to produce the Tahoe and Sequoia EFIs. Not the shipped configuration |

Kept out of the repo (see `.gitignore`): `EFI-private-Tahoe/` and `EFI-private-Sequoia/` (copies of the public EFIs that are identical except that their `config.plist` and profiles carry my real SMBIOS; `python -I tools/sync_private.py` keeps them in sync), the two ready-to-use zips built from them, `private_smbios.json`, `diagnostics/` (my ACPI dumps and hardware inventory), `backups/` and the macOS recovery image.

My two zips (not in the repo because they contain my SMBIOS):
* `LOQ15IAX9-TAHOE-26-OpenCore-1.0.8-EFI.zip` for macOS Tahoe
* `LOQ15IAX9-SEQUOIA-15-OpenCore-1.0.8-EFI.zip` for macOS Sequoia

Each has `EFI/` (copy it to the root of the USB stick, or `EFI/OC` onto the Windows ESP) and `profiles/`.

## Installing

1. Format a USB stick as GPT with one FAT32 partition (Basic data type) and copy the `EFI` folder for your macOS version to its root. First put your own generated SMBIOS values into `EFI/OC/config.plist` (see the SMBIOS section). For a fresh install, also put Apple's `com.apple.recovery.boot` folder (BaseSystem.dmg and BaseSystem.chunklist, made with OpenCore's `macrecovery.py -b Mac-7BA5B2D9E42DDD94 -m 00000000000000000 download`) on the root. Do not delete anything on your internal disks.
2. Set the BIOS as above. Plug in Ethernet (Recovery uses the Realtek driver).
3. F12, choose the stick, choose the Recovery image in OpenCore (it takes about 70 seconds to load the 884 MB image from a slow stick).
4. Disk Utility, Show All Devices: erase only the macOS volume as APFS (never the Windows disk, never the data volume). Reinstall macOS onto it.
5. After install: install NullMoth (the 1401 Mac app or the `nullmoth-nvidia` tarball installer), allow the extension in Privacy and Security, reboot twice.
6. Rename the macOS volume to MacOS if you like, so the picker label matches: `diskutil rename "MACOSTARGET" "MacOS"`.

To update from Sequoia to Tahoe I switched the EFI to the Tahoe one first (iBridged is what lets the OTA update work), updated macOS, then fixed Wi-Fi and audio as described above.

## Mount, copy and unmount the Windows ESP from Windows (administrator PowerShell)

Run this from the folder that holds your finished EFI (the SMBIOS in its `config.plist` filled in). I run it from my private copy. Replace `Tahoe` with `Sequoia` for the other OS.

```powershell
mountvol S: /S                                   # mounts the EFI System Partition of the boot disk as S:
Get-PSDrive S                                    # check free space (needs about 40 MB)
Get-ChildItem S:\EFI                             # expect Microsoft
if (Test-Path S:\EFI\OC) { Copy-Item -Recurse S:\EFI\OC "D:\ESP-OC-backup-$(Get-Date -Format yyyyMMdd-HHmm)"; Remove-Item -Recurse -Force S:\EFI\OC }
Copy-Item -Recurse .\EFI-private-Tahoe\OC S:\EFI\OC
Get-Item S:\EFI\OC\config.plist, S:\EFI\OC\OpenCore.efi
mountvol S: /D                                   # unmount
```
Never touch `S:\EFI\Microsoft`.

## Make OpenCore the main EFI (boot without the USB stick)

The macOS disk (Intel SSD) has no EFI partition, so OpenCore needs somewhere to live. Options:

Option A, put OpenCore on the Windows ESP (adds a folder, does not touch `\EFI\Microsoft`):
1. Check free space on the ESP first (needs about 40 MB for `EFI\OC`; my ESP is 260 MB).
2. Copy the folder with the commands above. Do not overwrite `S:\EFI\BOOT\BOOTX64.EFI` if one exists.
   The same copy can be done from macOS: run `diskutil list`, find the roughly 272 MB partition named EFI on the 512 GB Windows disk (the one that also holds the 509 GB Microsoft Basic Data and the 2 GB recovery partition), then:
```bash
sudo diskutil mount /dev/diskXs1            # replace diskXs1 with that partition
df -h /Volumes/EFI                          # check free space first
ls /Volumes/EFI/EFI                         # should show Microsoft
sudo cp -R /Volumes/1401/EFI/OC /Volumes/EFI/EFI/OC
sudo diskutil unmount /Volumes/EFI
```
3. Add a firmware boot entry and put it first (from Windows, administrator PowerShell):
```powershell
bcdedit /copy "{bootmgr}" /d "OpenCore"          # prints a GUID
bcdedit /set "{GUID}" path \EFI\OC\OpenCore.efi
bcdedit /set "{fwbootmgr}" displayorder "{GUID}" /addfirst
mountvol S: /D
```
   Alternative to step 3: set `Misc > Boot > LauncherOption` to `Full` and boot OpenCore once; it writes its own first boot entry (needs RequestBootVarRouting, already on).
4. Keep the USB stick as a fallback until you have rebooted a few times. If logging is on, logs will now be written to the ESP, so delete old `opencore-*.txt` files occasionally or turn logging off (below).

Option B, create a small ESP on the Intel disk: this needs shrinking a partition. I did not do it because I did not want to resize anything.

If something goes wrong, F12 and boot Windows Boot Manager directly. It is unchanged.

## Autoboot a selection, quiet boot, no logs

The shipped config is already quiet (no `-v`, no OpenCore log, no panic file). For a 5 second autoboot use the autoboot profile. To bring logging back use the debug profile. Copy the one you want over `EFI/OC/config.plist` (with your own SMBIOS values in it). By hand:

| Goal | Change |
|---|---|
| Pick a default entry | In the picker highlight the entry and press Ctrl+Enter (AllowSetDefault is on). It is stored in NVRAM, so an NVRAM reset clears it |
| Autoboot after N seconds | `Misc > Boot > Timeout` = N (0 waits forever). The picker is visible during the countdown; any key press stops it |
| Boot the default with no picker at all | `Misc > Boot > ShowPicker` = false and `TakeoffDelay` = 10000. Then hold Escape (or the 0 key) right after the Lenovo logo to bring the picker up. These keys come from the OpenCore documentation and I have not tested them on this keyboard |
| No verbose boot | Remove `-v` from `NVRAM > Add > 7C436110-AB2A-4BBB-A880-FE41995C9F82 > boot-args` |
| No kernel debug output | Remove `debug=0x100 msgbuf=1048576` from boot-args (keep `keepsyms=1` on Tahoe, SimpleHDA needs it). Note: `debug=0x100` stops the machine rebooting on a panic, so remove it only when things are stable |
| No OpenCore on-screen log | `Misc > Debug > Target` = 0 (0x41 keeps file logging only; 0x43 adds on-screen) |
| No OpenCore log files at all | `Target` = 0, `AppleDebug` = false, `SysReport` = false |
| Faster picker | Swap `OpenCore.efi` and the drivers for the RELEASE build of the same version (1.0.8) |

## Logs (only with the debug profile; the shipped config has them off)

| Log | Where |
|---|---|
| OpenCore log (includes the boot.efi log) | `opencore-YYYY-MM-DD-HHMMSS.txt` in the root of the volume OpenCore booted from |
| OpenCore panic copy | `panic-YYYY-MM-DD-HHMMSS.txt` in the same place |
| Verbose boot | On screen with `-v`; later `log show --boot` in macOS |
| macOS panics | `/Library/Logs/DiagnosticReports` |
| NullMoth | 1401 app, Crash report, Send logs |

SysReport (ACPI, SMBIOS dumps) is off. It contains the real machine SMBIOS, so never post it.

## SMBIOS

Generate your own with corpnewt/GenSMBIOS for MacBookPro16,2 and put the serial, board serial, UUID and ROM into your `config.plist`. Mine are unique to my build and are not in this repo. Never share your plist or logs. Apple's coverage page (checkcoverage.apple.com) is the way to check the serial is not a real registered Mac. It needs a CAPTCHA, so do that by hand.

## Sleep and hibernation

The NullMoth driver cannot wake the GPU after sleep, so I switch sleep and hibernation off in macOS. OpenCore already has `Misc > Boot > HibernateMode` = None.

```bash
sudo pmset -a hibernatemode 0
sudo pmset -a standby 0
sudo pmset -a autopoweroff 0
sudo pmset -a powernap 0
sudo pmset -a disablesleep 1          # no system sleep at all (closing the lid will not sleep either)
sudo rm -f /var/vm/sleepimage         # optional, frees the RAM-sized hibernation file
pmset -g | grep -E "hibernatemode|standby|autopoweroff|SleepDisabled"
```

To undo: `sudo pmset -a disablesleep 0 hibernatemode 3 standby 1 autopoweroff 1`. For Windows hibernation (and Fast Startup) run `powercfg /h off` in an administrator prompt.

## Hybrid mode alternative: NMIntelFB (Sequoia era, not run)

If I stay in Hybrid mode (no BIOS change) the internal panel is on the Intel iGPU, which macOS cannot drive. There is a route that keeps the panel on the iGPU while the NVIDIA GPU does all the rendering: NullMoth's NMIntelFB framebuffer, patched and built with nmx-intel (kitsuneislife/nmx-intel), on NullMoth driver 2.3.6 (newer releases blink on that route). I adapted a working Tiger Lake write-up for my machine. From the sources, my iGPU (8086:468B) is in NMIntelFB's accepted list and my RTX 2050 is in the 2.3.6 installer's table, but I have not run it, and it was only ever looked at for Sequoia. The guide is `docs/HYBRID-NMINTELFB.md`, the config is `profiles/Sequoia/config-hybrid-NMIntelFB.plist` (the opposite iGPU handling to the shipped profile: no iGPU hiding, no IONDRVSupport block), and the build and install helpers are in `tools/macos/`.

Costs: one display only, no sleep, about 45 seconds extra per boot, and I stay on NullMoth 2.3.6. WhateverXe (Iris Xe acceleration) is the other iGPU option; I tried it with NullMoth and it hung at the HID driver stage, so it is not used here.

## Not verified yet

* The Windows entry device path (computed from my partition table) and whether Windows keeps the Lenovo identity when launched through OpenCore.
* Sleep and hibernation (not supported by the driver).
* The Sequoia EFI since the move to Tahoe (I have not booted it again).
* Wi-Fi on Tahoe uses an alpha build; I will watch for regressions after NullMoth or macOS updates.

## Credits and sources

OpenCorePkg, Lilu, VirtualSMC, AppleALC, NVMeFix, RestrictEvents, VoodooPS2 and CpuTscSync by Acidanthera. VoodooI2C by the VoodooI2C team. NullMoth NVIDIA driver and 1401 by NullMoth Systems. AirportItlwm and IntelBluetoothFirmware by OpenIntelWireless; the Tahoe AirportItlwm build and SimpleHDA by laobamac. iBridged by Carnations-Botanica. HoRNDIS by Joshua Wise. AMFIPass by Dortania/Acidanthera. GenSMBIOS by CorpNewt. Icons: Acidanthera GoldenGate and the chris1111 Flavours-AppleSet theme. nmx-intel by kitsuneislife (NMIntelFB patches, referenced above). The forum notes from jzrodriguez98 and kgp-macPro on Intel Wi-Fi for Tahoe helped me understand why the first Wi-Fi kext failed.

Special thanks to pranish-dev (https://github.com/pranish-dev/loq_hackintosh) for the laptop-specific patches this build started from and for being my main reference for the LOQ family.
