/*
 * Lenovo LOQ 15IAX9 - stops instant wake from USB/XHCI/XDCI (_PRW = GPRW(0x6D, 4)).
 * Pair with ACPI patch GPRW -> XPRW.  Firmware GPRW lives in Scope(\) of the DSDT.
 */
DefinitionBlock ("", "SSDT", 2, "LOQMAC", "GPRW", 0x00000000)
{
    External (XPRW, MethodObj)

    Method (GPRW, 2, NotSerialized)
    {
        If (_OSI ("Darwin"))
        {
            If ((Arg0 == 0x6D))
            {
                Return (Package (0x02)
                {
                    0x6D,
                    Zero
                })
            }

            If ((Arg0 == 0x0D))
            {
                Return (Package (0x02)
                {
                    0x0D,
                    Zero
                })
            }
        }

        Return (XPRW (Arg0, Arg1))
    }
}
