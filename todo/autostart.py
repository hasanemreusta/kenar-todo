"""Optional 'start with Windows' entry (per-user Run key). Only touched when the user toggles it."""
import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "TodoAppWidget"


def project_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _pythonw() -> str:
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = exe[:-len("python.exe")] + "pythonw.exe"
        if os.path.exists(candidate):
            return candidate
    return exe


def startup_command(pythonw: str = "", project: str = "") -> str:
    """Command line that launches the widget without a console window."""
    if getattr(sys, "frozen", False) and not pythonw:    # packaged exe: it launches itself
        return f'"{sys.executable}"'
    exe = pythonw or _pythonw()
    project = project or project_dir()
    code = f"import sys; sys.path.insert(0, r'{project}'); from todo.gui import main; main()"
    return f'"{exe}" -c "{code}"'


def is_packaged() -> bool:
    """True when running from a Microsoft Store (MSIX) install: startup is then a Windows setting, not a Run key."""
    return "\\WindowsApps\\" in (sys.executable or "")


def is_enabled() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, VALUE_NAME)
        return True
    except (ImportError, OSError):
        return False


def set_enabled(on: bool) -> bool:
    """Add or remove the Run entry; returns the new state."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if on:
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, startup_command())
            else:
                try:
                    winreg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
    except (ImportError, OSError):
        pass
    return is_enabled()
