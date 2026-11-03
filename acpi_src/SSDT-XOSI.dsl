/*
 * Lenovo LOQ 15IAX9 - the DSDT derives OSYS from _OSI("Windows 2001".."Windows 2022") and gates I2C
 * (touchpad), power-limit and thermal code on OSYS >= 0x07DF (Windows 2015).  Pair with ACPI patch
 * _OSI -> XOSI so macOS is told it is a recent Windows.
 */
DefinitionBlock ("", "SSDT", 2, "LOQMAC", "XOSI", 0x00000000)
{
    Method (XOSI, 1, NotSerialized)
    {
        If (_OSI ("Darwin"))
        {
            Local0 = Package (0x10)
                {
                    "Windows 2001",
                    "Windows 2001 SP1",
                    "Windows 2001.1",
                    "Windows 2001 SP2",
                    "Windows 2006",
                    "Windows 2009",
                    "Windows 2012",
                    "Windows 2013",
                    "Windows 2015",
                    "Windows 2016",
                    "Windows 2017",
                    "Windows 2017.2",
                    "Windows 2018",
                    "Windows 2020",
                    "Windows 2021",
                    "Windows 2022"
                }
            Return ((Ones != Match (Local0, MEQ, Arg0, MTR, Zero, Zero)))
        }

        Return (_OSI (Arg0))
    }
}
