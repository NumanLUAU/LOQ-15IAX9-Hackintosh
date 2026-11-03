# Troubleshooting

Collect first: `opencore-*.txt`, `panic-*.txt`, `SysReport/` from the USB root, and a photo of the last verbose lines.

| Symptom | Likely cause | What to do |
|---|---|---|
| USB not in F12 menu | Not GPT/FAT32, or `BOOTx64.efi` missing | Re-check `U:\EFI\BOOT\BOOTx64.efi`; disable Secure Boot/CSM |
| No picker, stuck on logo | GOP/resolution issue | In `config.plist`: `UEFI->Output->Resolution = 1920x1080@32`, or `ConsoleMode = ""` |
| Picker shows no Recovery | Recovery folder misplaced / ScanPolicy | Folder must be `U:\com.apple.recovery.boot\BaseSystem.{dmg,chunklist}`; partition must be Basic-data FAT32; set `ScanPolicy` to `0` temporarily |
| Windows entry fails ("failed to load") | Computed device path is wrong | `OpenShell` -> `map -r`, find the FS with `\EFI\Microsoft`, rebuild `Path` (disk 0 WD SN5000S). Meanwhile use F12 -> Windows Boot Manager |
| Windows shows Apple model | Custom SMBIOS GUID not effective | Use the firmware boot entry for Windows; tell me the log |
| Stops at `EXITBS:START` / `[EB\|#LOG:EXITBS:START]` | CPU topology / memory map. Check HT is **off**; try `Booter->Quirks` changes: `DevirtualiseMmio` off, add `MmioWhitelist`, or `ProvideMaxSlide=1` | Send `opencore-*.txt`; keep other changes minimal |
| `Still waiting for root device` | USB map/NVMe | NVMe: make sure `Standard NVM Express` (not RST/VMD) in BIOS; USB: keep `XhciPortLimit=true`; boot from a port that works |
| Panic `cpu_thread_alloc` / `x86_validate_topology` | Hyper-Threading is on | BIOS HT off (4P+4E = 8 threads) |
| Panic `TSC`/`Wait for ... timeout`/random in early boot | TSC desync | `CpuTscSync` is on; send panic file |
| `AppleACPIPlatform` / EC panic | EC SSDT/path | Remove `SSDT-EC-USBX` and rebuild with `\_SB.PC00.LPCB`; send log |
| Black screen after verbose text (profile A) | Firmware framebuffer lost at handoff | Try the other BIOS graphics mode (Hybrid <-> dGPU-only), send the photo + `opencore-*.txt` |
| Black screen with NullMoth (B/C/E) | Panel not on dGPU, BAR, AMFI, SIP | Profile B requires BIOS dGPU-only; drop `nvrmacpibl`; set `ResizeAppleGpuBars=0`; use *1401: Remove NVIDIA driver* picker entry (Mac app) or boot with `-nvoff`; revert to profile A |
| Panic in WindowServer / `IOFramebuffer::postOpen` with WG | `gfxrst=4` missing | Only relevant to profile E (already set) |
| WhateverXe: no display on panel | eDP unsupported on ADL-HX | Expected risk; switch to B or A |
| No Wi-Fi | Sonoma-14.4 AirportItlwm may not attach on 15.x | Use Ethernet; swap to `itlwm.kext` 2.3.0 + HeliPort (disable AirportItlwm) |
| No Android tethering | HoRNDIS 9.2 is old | Enable USB tethering on phone, check `systemextensions`/Privacy prompts, send log |
| Touchpad dead | I2C interrupt mode | Keep `-vi2c-force-polling`; VoodooI2C DEBUG log: `-liludbgall`; confirm `ioreg -l | grep GXTP5100` |
| Brightness keys do nothing | No PNLF (A/B/C) | iGPU profiles use `SSDT-PNLF`; B: try `nvrmacpibl=1` once |
| Stuck after NVRAM reset | Lenovo firmware quirk (OpenCore #995) | Power off 30 s, F2 -> Load defaults; F12 -> Windows Boot Manager |
| Need to undo everything | - | Remove the USB. The internal disks only changed where **you** erased `MACOSTARGET`. |

Safe-mode toggles you can use without a rebuild: edit boot-args in `config.plist` (PlistEdit/ProperTree) - remove NullMoth args to fall back to profile-A behaviour.
