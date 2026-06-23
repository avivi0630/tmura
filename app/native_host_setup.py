#!/usr/bin/env python3
"""
Tmura - Native Messaging Host setup
Registers the Chrome Native Messaging host using a user-writable directory
so it works even when the app is installed under Program Files.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple

from app_config import HOST_NAME, EXTENSION_ID, get_config_dir, get_install_dir


def find_system_python() -> str:
    """Locate a usable system Python interpreter (not the PyInstaller exe)."""
    if not getattr(sys, "frozen", False):
        return sys.executable

    for name in ("python", "python3", "py"):
        found = shutil.which(name)
        if found:
            try:
                r = subprocess.run(
                    [found, "--version"],
                    capture_output=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
                )
                if r.returncode == 0:
                    return found
            except Exception:
                continue
    return sys.executable


def get_native_host_dir() -> Path:
    """User-writable directory for the manifest and wrapper."""
    host_dir = get_config_dir() / "native_host"
    host_dir.mkdir(parents=True, exist_ok=True)
    return host_dir


def write_manifest_and_wrapper(host_dir: Path) -> Tuple[str, str]:
    """Write host_wrapper.{bat,sh} and the JSON manifest into host_dir.
    Returns (manifest_path, wrapper_path)."""
    install_dir = get_install_dir()
    host_py = install_dir / "app" / "host.py"

    if not host_py.exists():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "app" / "host.py"
            if bundled.exists():
                host_py = bundled

    python_exe = find_system_python()

    if platform.system() == "Windows":
        wrapper_path = host_dir / "host_wrapper.bat"
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write("@echo off\r\n")
            f.write(f'"{python_exe}" "{host_py}" %*\r\n')
    else:
        wrapper_path = host_dir / "host_wrapper.sh"
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n")
            f.write(f'exec "{python_exe}" "{host_py}" "$@"\n')
        try:
            wrapper_path.chmod(0o755)
        except Exception:
            pass

    manifest = {
        "name": HOST_NAME,
        "description": "Tmura Native Host",
        "path": str(wrapper_path),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{EXTENSION_ID}/"],
    }
    manifest_path = host_dir / f"{HOST_NAME}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return str(manifest_path), str(wrapper_path)


def is_native_host_installed() -> bool:
    if platform.system() == "Windows":
        try:
            import winreg
            reg_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
            value, _ = winreg.QueryValueEx(key, "")
            winreg.CloseKey(key)
            if os.path.exists(value):
                with open(value, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                expected = f"chrome-extension://{EXTENSION_ID}/"
                return expected in manifest.get("allowed_origins", [])
            return False
        except FileNotFoundError:
            return False
        except Exception:
            return False
    elif platform.system() == "Darwin":
        mp = Path.home() / "Library/Application Support/Google/Chrome/NativeMessagingHosts" / f"{HOST_NAME}.json"
        return mp.exists()
    elif platform.system() == "Linux":
        mp = Path.home() / ".config/google-chrome/NativeMessagingHosts" / f"{HOST_NAME}.json"
        return mp.exists()
    return False


def register_native_host() -> Tuple[bool, str]:
    """Create manifest+wrapper in a user-writable dir, then register in HKCU.
    Returns (success, manifest_path_on_success or prefixed error string)."""
    try:
        host_dir = get_native_host_dir()
        manifest_path, _ = write_manifest_and_wrapper(host_dir)
    except PermissionError as e:
        return False, f"PERMISSION: {e}"
    except Exception as e:
        return False, f"WRITE_FAIL: {e}"

    if platform.system() == "Windows":
        try:
            import winreg
            reg_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, manifest_path)
            winreg.CloseKey(key)
        except Exception as e:
            return False, f"REG_FAIL: {e}"
    else:
        if platform.system() == "Darwin":
            md = Path.home() / "Library/Application Support/Google/Chrome/NativeMessagingHosts"
        else:
            md = Path.home() / ".config/google-chrome/NativeMessagingHosts"
        md.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_path, md / f"{HOST_NAME}.json")

    return True, manifest_path
