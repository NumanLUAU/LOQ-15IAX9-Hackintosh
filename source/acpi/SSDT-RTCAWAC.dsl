/*
 * Lenovo LOQ 15IAX9 - firmware exposes the ACPI000E AWAC clock when STAS == 0 and the legacy
 * PNP0B00 RTC when STAS == 1 (see DSDT: _SB.AWAC._STA / _SB.PC00.LPCB.RTC._STA).  macOS has no
 * AWAC driver, so force the RTC path under Darwin only.
 */
DefinitionBlock ("", "SSDT", 2, "LOQMAC", "RTCAWAC", 0x00000000)
{
    External (STAS, IntObj)

    Scope (\)
    {
        Method (_INI, 0, NotSerialized)  // _INI: Initialize
        {
            If (_OSI ("Darwin"))
            {
                STAS = One
            }
        }
    }
}
