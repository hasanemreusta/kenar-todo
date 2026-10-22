"""Only one widget at a time: a second launch exits quietly instead of stacking another pill on screen."""
import sys

_HELD = {}   # name -> handle (kept alive for the life of the process)


def acquire(name: str = "TodoAppWidget") -> bool:
    """True if this process is the first (and now only) instance; False if another one already runs."""
    if name in _HELD:
        return False
    if sys.platform != "win32":
        _HELD[name] = None
        return True
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, "Local\\" + name)
    if not handle:
        return True      # could not create a lock: do not block the user
    if kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(ctypes.c_void_p(handle))
        return False
    _HELD[name] = handle
    return True
