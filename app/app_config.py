#!/usr/bin/env python3
"""
Tmura - Application Configuration
Persists settings to a platform-appropriate config directory
"""

import json
import os
import sys
import platform
from pathlib import Path
from typing import Any, Dict, Optional

APP_NAME = "Tmura"
CONFIG_FILENAME = "config.json"

EXTENSION_ID = "mefmiammilbcjogoclncpjcbpklgljal"
CHROME_STORE_URL = f"https://chromewebstore.google.com/detail/smart-converter/{EXTENSION_ID}"
HOST_NAME = "com.compressor.host"


def get_config_dir() -> Path:
    """Get platform-specific config directory (always user-writable)"""
    system = platform.system()

    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        config_dir = Path(base) / APP_NAME
    elif system == "Darwin":
        config_dir = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
        config_dir = Path(xdg) / APP_NAME

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    return get_config_dir() / CONFIG_FILENAME


def get_base_dir() -> Path:
    """Base directory - handles both dev and PyInstaller frozen modes"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent.resolve()


def get_install_dir() -> Path:
    """Project root directory (where launcher.py lives)"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.resolve()


def get_native_host_dir() -> Path:
    """User-writable directory for native messaging host files (manifest + wrapper).
    Always writable regardless of install location (Program Files, /Applications, etc.)."""
    return get_config_dir() / "native_host"


def get_icon_path() -> Optional[str]:
    """Find icon.ico - internal (bundled) or external (next to exe)"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled = Path(sys._MEIPASS) / "icon.ico"
        if bundled.exists():
            return str(bundled)

    if getattr(sys, 'frozen', False):
        ext = Path(sys.executable).parent / "icon.ico"
        if ext.exists():
            return str(ext)

    install_dir = Path(__file__).parent.parent.resolve()
    candidates = [
        install_dir / "app" / "resources" / "icon.ico",
        install_dir / "app" / "icon.ico",
        install_dir / "icon.ico",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


DEFAULT_CONFIG: Dict[str, Any] = {
    "language": "he",
    "minimize_to_tray": True,
    "start_with_windows": False,
    "background_server": False,
    "output_dir": "",
    "last_quality": 80,
}


class AppConfig:
    _instance = None

    def __init__(self):
        self._data: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self._load()

    @classmethod
    def instance(cls) -> "AppConfig":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self):
        path = get_config_path()
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                self._data.update(saved)
            except Exception:
                pass

    def save(self):
        path = get_config_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self.save()

    @property
    def language(self) -> str:
        return self._data.get("language", "he")

    @language.setter
    def language(self, value: str):
        self._data["language"] = value
        self.save()

    @property
    def minimize_to_tray(self) -> bool:
        return self._data.get("minimize_to_tray", True)

    @minimize_to_tray.setter
    def minimize_to_tray(self, value: bool):
        self._data["minimize_to_tray"] = value
        self.save()

    @property
    def background_server(self) -> bool:
        return self._data.get("background_server", False)

    @background_server.setter
    def background_server(self, value: bool):
        self._data["background_server"] = value
        self.save()

    @property
    def output_dir(self) -> str:
        return self._data.get("output_dir", os.path.expanduser("~/Desktop/Converted"))

    @output_dir.setter
    def output_dir(self, value: str):
        self._data["output_dir"] = value
        self.save()
