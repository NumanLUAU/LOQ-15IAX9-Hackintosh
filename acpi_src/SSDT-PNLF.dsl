/*
 * Lenovo LOQ 15IAX9 - backlight device for the Intel iGPU profile (WhateverXe).
 * Intel PCH-PWM style (CFL+/ADL) PNLF; iGPU is \_SB.PC00.GFX0 (_ADR 0x00020000).
 * Only enabled in the iGPU / hybrid profiles.
 */
DefinitionBlock ("", "SSDT", 2, "LOQMAC", "PNLF", 0x00000000)
{
    External (_SB_.PC00.GFX0, DeviceObj)

    Scope (\_SB)
    {
        Device (PNLF)
        {
            Name (_HID, EisaId ("APP0002"))  // _HID: Hardware ID
            Name (_CID, "backlight")  // _CID: Compatible ID
            Name (_UID, 0x13)  // _UID: Unique ID
            Method (_STA, 0, NotSerialized)  // _STA: Status
            {
                If (_OSI ("Darwin"))
                {
                    Return (0x0B)
                }
                Else
                {
                    Return (Zero)
                }
            }
        }
    }
}
