"""System-wide quick-add shortcut on Windows (user-selectable, default Ctrl+Alt+N).

A background thread owns the hotkey and its message loop; presses are put on a queue that the
Tk thread polls (Tk itself must only be touched from its own thread).
"""
import queue
import sys
import threading

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x0001, 0x0002, 0x0004, 0x4000
VK_SPACE, VK_N = 0x20, 0x4E
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012
HOTKEY_ID = 0x5A11

# name -> (modifiers, virtual key, label shown to the user)
HOTKEYS = {
    "ctrl_alt_n": (MOD_CONTROL | MOD_ALT, VK_N, "Ctrl+Alt+N"),
    "ctrl_shift_space": (MOD_CONTROL | MOD_SHIFT, VK_SPACE, "Ctrl+Shift+Boşluk"),
    "ctrl_alt_space": (MOD_CONTROL | MOD_ALT, VK_SPACE, "Ctrl+Alt+Boşluk"),
    "off": (0, 0, "Kapalı"),
}
DEFAULT = "ctrl_alt_n"


class GlobalHotkey:
    def __init__(self, name=DEFAULT):
        self.name = name if name in HOTKEYS else DEFAULT
        self.modifiers, self.key, self.label = HOTKEYS[self.name]
        self.presses = queue.Queue()
        self.registered = threading.Event()
        self.failed = threading.Event()
        self._thread_id = None

    def start(self) -> bool:
        """Register in a daemon thread; False if switched off, not on Windows, or taken by another program."""
        if self.name == "off" or sys.platform != "win32":
            return False
        threading.Thread(target=self._run, daemon=True).start()
        while not (self.registered.is_set() or self.failed.is_set()):
            self.registered.wait(0.05)
        return self.registered.is_set()

    def _run(self):
        import ctypes
        from ctypes import wintypes
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, HOTKEY_ID, self.modifiers | MOD_NOREPEAT, self.key):
            self.failed.set()
            return
        self.registered.set()
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.presses.put(True)
        user32.UnregisterHotKey(None, HOTKEY_ID)

    def stop(self):
        """Release the shortcut (ends the message loop, which unregisters it)."""
        if self._thread_id and self.registered.is_set():
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            self.registered.clear()

    def pressed(self) -> bool:
        """True (once per press) if the shortcut was pressed since the last call."""
        hit = False
        while not self.presses.empty():
            self.presses.get_nowait()
            hit = True
        return hit
