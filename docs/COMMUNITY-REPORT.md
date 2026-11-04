**Hardware**
- Laptop: Lenovo LOQ 15IAX9 (83GS)
- CPU: Intel Core i5-12450HX (Alder Lake-HX, 4P + 4E, Hyper-Threading off, 8 threads)
- dGPU: NVIDIA GeForce RTX 2050 Laptop 4 GB `10de:25ed` (GA107, Ampere)
- iGPU: Intel UHD Graphics `8086:468b` (disabled, BIOS dGPU only)
- 12 GB DDR5-4800, WD SN5000S + Intel 660p NVMe
- Wi-Fi/Bluetooth: Intel AX203 (CNVi)
- OpenCore 1.0.8, SMBIOS MacBookPro16,2

**Software**
- macOS Tahoe 26.x (also ran on Sequoia 15.x before I updated)
- NullMoth driver 2.6.6 (installed and updated with the 1401 Mac app)

**BIOS**
- Graphics Device: dGPU only (this laptop has a MUX switch)
- Hyper-Threading: Off, Secure Boot: Off, CSM: Off, VT-d: Off (or on with `DisableIoMapper`)

**Result**
Full Metal acceleration on the RTX 2050. In dGPU-only mode the built-in panel (1920x1080, 144 Hz) and the HDMI monitor both register on the NVIDIA GPU, so dual display works. In Hybrid mode the built-in panel is wired to the Intel iGPU, macOS does not recognize it, and only the HDMI port works on the NVIDIA GPU.

**What works (Tahoe)**
- Built-in display and HDMI display at the same time, both on the NVIDIA GPU
- Brightness control (`nvrmacpibl=1`)
- Keyboard, mouse, USB, Thunderbolt/USB-C, Ethernet
- Touchpad (Goodix I2C, needs a VoodooI2C match for the Alder Lake controller `8086:7acc`, see below)
- Audio and microphone (ALC257, AppleALC layout 99 plus SimpleHDA)
- Wi-Fi with the native menu, no HeliPort (laobamac AirportItlwm Tahoe build)
- Bluetooth (`-ibtcompatbeta` and two NVRAM keys, see below)
- Android USB tethering (HoRNDIS)
- macOS OTA updates (iBridged)

**What does not work**
- Sleep and hibernation (NullMoth black screen on wake). I run `pmset` with sleep and hibernation off.
- WhateverXe together with NullMoth: the boot stuck waiting for the HID driver, so I removed it.

**Tahoe specific notes**
- Audio: Tahoe has no AppleHDA. Adding laobamac's SimpleHDA 1.0.0 after AppleALC (order Lilu, AppleALC, SimpleHDA) with `keepsyms=1` brought it back. VoodooHDA on Tahoe has to be built and installed on the Mac, so I did not use it.
- Wi-Fi: AirportItlwm-Tahoe 1.0.0 (kgp-macPro) needs OCLP-CustoMac root patches and gave me no interface and no MAC address. laobamac's itlwm v2.4.0-alpha Tahoe build works with no root patches. Keep it limited to Darwin 25.x.
- Bluetooth: on Tahoe `-ibtcompatbeta` is needed on top of IntelBluetoothFirmware, IntelBTPatcher 2.5.0 and BlueToolFixup 2.7.3.
- Updating from Sequoia: iBridged 1.0.1 (Lilu plugin) fixes the OTA process, and RestrictEvents RELEASE 1.1.6 with `revpatch=sbvmm` was used.

**Notes for other Alder Lake (12th gen) laptop owners**
- CPUID spoof to Comet Lake (`Cpuid1Data` 55 06 0A 00, mask FF FF FF FF), `ProvideCurrentCpuInfo`, `CpuTscSync`, Hyper-Threading off in BIOS.
- Page fault at `0xFF04504C` right after the hand-off to the kernel: add a `MmioWhitelist` entry for `0xFF000000` (needed with `DevirtualiseMmio`).
- If the screen shows `DSDT table load failed` and everything stops, the old ACPI interpreter in macOS is choking on a conditionally defined USB port scope. I fixed it with a same-length ACPI patch on the DSDT instead of a replacement DSDT.
- If boot hangs after AppleCredentialManager, the DSDT may declare CPUs only as `Device()` objects. An SSDT that adds `Processor()` objects (SSDT-PLUG-ALT style) fixed it.
- Touchpad: official VoodooI2C 2.9.1 does not match the Alder Lake-S I2C controller `8086:7acc`. Adding `0x7acc8086&0xFFFCFFFF` to the `IOPCIMatch` of the `VoodooI2CPCILakeController` personality fixed it (polling mode, `-vi2c-force-polling`).
- Bluetooth: it appeared in System Settings but turned itself off a few seconds after enabling. Adding `bluetoothExternalDongleFailed` (00) and `bluetoothInternalControllerInfo` (14 zero bytes) to NVRAM Add and NVRAM Delete fixed it.
- On Sequoia the official AirportItlwm 2.3.0 Sonoma 14.4 build fails vtable patching; a newer third-party build works.
- NullMoth specifics: SIP `0x0A43`, AMFIPass, `Kernel > Block` for `com.apple.iokit.IONDRVSupport` in dGPU-only mode, `ResizeGpuBars` and `ResizeAppleGpuBars` set to -1.

Two EFIs (Tahoe and Sequoia) and a full write-up of what changed for Alder Lake and what changed for this laptop: see my repo.

Big thanks to NullMoth for the driver, to laobamac for the Tahoe Wi-Fi and audio work, and to pranish-dev for the LOQ reference EFI and laptop-specific patches.
