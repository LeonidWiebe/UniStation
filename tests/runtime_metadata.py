"""Read loaded native library paths; detect accidental DLL mixing on Windows."""
import os


def native_modules():
    if os.name != "nt":
        return {}
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel.GetModuleHandleW.restype = wintypes.HMODULE
    kernel.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    kernel.GetModuleFileNameW.restype = wintypes.DWORD
    result = {}
    for name in ("FreeCADGui.dll", "FreeCADApp.dll", "FreeCADBase.dll",
                 "Qt6Core.dll", "Coin4.dll", "python311.dll"):
        handle = kernel.GetModuleHandleW(name)
        buffer = ctypes.create_unicode_buffer(32768)
        result[name] = buffer.value if handle and kernel.GetModuleFileNameW(
            handle, buffer, len(buffer)) else None
    return result
