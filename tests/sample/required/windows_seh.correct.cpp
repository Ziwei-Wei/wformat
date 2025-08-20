// format_topic05_windows_seh.cpp
// Standalone formatting test: emulates a tiny subset of Win32 SEH-related
// constructs so it can compile on non-Windows platforms without <windows.h>.
//
// Focus patterns:
//  - Conditional SEH (__try/__except) vs portable fallback
//  - Win32-style typedefs (BYTE, DWORD)
//  - Macro style for EXCEPTION handling & UNREFERENCED_PARAMETER
//  - Simple buffer "decode" loop resembling license decode style

#include <iostream>

// -----------------------------------------------------------------------------
// Minimal Win32-ish typedefs & macros (no real Windows dependency)
// -----------------------------------------------------------------------------
using BYTE  = unsigned char;
using DWORD = unsigned long;

#ifndef EXCEPTION_EXECUTE_HANDLER
#define EXCEPTION_EXECUTE_HANDLER 1
#endif

#define UNREFERENCED_PARAMETER(x) (void) (x)

// Portable abstraction over SEH:
// On MSVC we use real __try/__except; elsewhere we map to try/catch(...)
#ifdef _MSC_VER
#define TRY_BLOCK    __try
#define EXCEPT_BLOCK __except (EXCEPTION_EXECUTE_HANDLER)
#else
#define TRY_BLOCK    try
#define EXCEPT_BLOCK catch (...)
#endif

// -----------------------------------------------------------------------------
// Function under test
// -----------------------------------------------------------------------------
int
DecodeBuffer(
    const BYTE* pb,
    DWORD cb
    )
{
    BYTE tmp[16] = {};

    if (cb > sizeof(tmp))
    {
        return -1;
    }

    TRY_BLOCK
    {
        for (DWORD i = 0; i < cb; ++i)
        {
            // Simple reversible transform (XOR) to mimic “decrypt” loop style
            tmp[i] = static_cast<BYTE>(pb[i] ^ 0xAA);
        }
    }
    EXCEPT_BLOCK
    {
        return -2;
    }

    return tmp[0];
}

// -----------------------------------------------------------------------------
// Entry point
// -----------------------------------------------------------------------------
int
main()
{
    BYTE data[4] = {1, 2, 3, 4};
    int r        = DecodeBuffer(
        data,
        4
        );
    std::cout << "result=" << r << "\n";

    return 0;
}