#!/usr/bin/env python3
"""
Tmura - Single instance enforcement.
Windows: named mutex + hidden message window.
Other: lock file + signal file.
"""

import platform
import struct
import ctypes
from pathlib import Path

_mutex_handle = None
_lock_file = None
_lock_fd = None

WM_TMURA_SHOW = 0x8000 + 0x0100  # WM_APP range, safe custom message


def check_single_instance() -> bool:
    """Returns True if this is the first instance, False if another is already running."""
    if platform.system() == "Windows":
        return _check_single_instance_windows()
    else:
        return _check_single_instance_unix()


def _check_single_instance_windows() -> bool:
    global _mutex_handle
    import ctypes
    mutex_name = "Global\\TmuraSingleInstance_v3"
    kernel32 = ctypes.windll.kernel32
    _mutex_handle = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        return False
    return True


def _check_single_instance_unix() -> bool:
    global _lock_fd
    import fcntl
    lock_file = Path.home() / ".tmura.lock"
    try:
        _lock_fd = open(lock_file, "w")
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (IOError, OSError):
        return False


def signal_existing_instance():
    """Tell the already-running instance to raise its window."""
    if platform.system() == "Windows":
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW("TmuraMsgWnd", None)
        if hwnd:
            user32.PostMessageW(hwnd, WM_TMURA_SHOW, 0, 0)
    else:
        signal_file = Path.home() / ".tmura_show_signal"
        try:
            signal_file.touch()
        except Exception:
            pass


def register_show_window_callback(window):
    """Register mechanism so another instance can tell this one to show."""
    if platform.system() == "Windows":
        _register_windows(window)
    else:
        _register_unix(window)


def _register_windows(window):
    import ctypes
    import ctypes.wintypes as wintypes
    from PyQt6.QtCore import Qt, QTimer

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Define WNDCLASSEXW manually (wintypes.WNDCLASS is not available in all builds)
    WNDPROC = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    )

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize",        wintypes.UINT),
            ("style",         wintypes.UINT),
            ("lpfnWndProc",   WNDPROC),
            ("cbClsExtra",    ctypes.c_int),
            ("cbWndExtra",    ctypes.c_int),
            ("hInstance",     wintypes.HINSTANCE),
            ("hIcon",         wintypes.HANDLE),
            ("hCursor",       wintypes.HANDLE),
            ("hbrBackground", wintypes.HANDLE),
            ("lpszMenuName",  wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
            ("hIconSm",       wintypes.HANDLE),
        ]

    def _wnd_proc(hwnd, msg, wparam, lparam):
        if msg == WM_TMURA_SHOW:
            window.show()
            window.raise_()
            window.activateWindow()
            state = window.windowState()
            window.setWindowState(
                (state & ~Qt.WindowState.WindowMinimized)
                | Qt.WindowState.WindowActive
            )
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    wnd_proc_ref = WNDPROC(_wnd_proc)
    window._wnd_proc_ref = wnd_proc_ref  # keep alive

    class_name = "TmuraMsgWnd"
    hinstance = kernel32.GetModuleHandleW(None)

    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wc.lpfnWndProc = wnd_proc_ref
    wc.hInstance = hinstance
    wc.lpszClassName = class_name

    user32.RegisterClassExW(ctypes.byref(wc))

    # HWND_MESSAGE = -3 (message-only window, invisible)
    HWND_MESSAGE = wintypes.HWND(-3)
    msg_hwnd = user32.CreateWindowExW(
        0, class_name, "TmuraMsgWindow", 0,
        0, 0, 0, 0,
        HWND_MESSAGE, None, hinstance, None
    )
    window._msg_hwnd = msg_hwnd

    # Pump messages for the hidden window periodically
    def _pump_messages():
        msg = wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), msg_hwnd, 0, 0, 0x0001):  # PM_REMOVE
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    timer = QTimer()
    timer.timeout.connect(_pump_messages)
    timer.start(200)
    window._win_msg_timer = timer


def _register_unix(window):
    from PyQt6.QtCore import Qt, QTimer
    signal_file = Path.home() / ".tmura_show_signal"

    def _check_signal():
        if signal_file.exists():
            try:
                signal_file.unlink()
            except Exception:
                pass
            window.show()
            window.raise_()
            window.activateWindow()
            state = window.windowState()
            window.setWindowState(
                (state & ~Qt.WindowState.WindowMinimized)
                | Qt.WindowState.WindowActive
            )

    timer = QTimer()
    timer.timeout.connect(_check_signal)
    timer.start(500)
    window._signal_timer = timer
