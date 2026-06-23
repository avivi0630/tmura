#!/usr/bin/env python3
"""
Tmura - Full Installer
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

from app_config import CHROME_STORE_URL, get_install_dir
from native_host_setup import register_native_host


def install_dependencies():
    print("\n" + "=" * 50)
    print("Installing Python dependencies...")
    print("=" * 50)
    req_file = get_install_dir() / "requirements.txt"
    if req_file.exists():
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        print("Dependencies installed" if result.returncode == 0 else "Error installing dependencies")
    else:
        print("requirements.txt not found")


def install_native_host():
    print("\n" + "=" * 50)
    print("Installing Native Messaging Host...")
    print("=" * 50)
    success, result = register_native_host()
    if success:
        print(f"Native Host registered: {result}")
    else:
        print(f"Native Host registration failed: {result}")


def show_extension_instructions():
    print("\n" + "=" * 50)
    print("Chrome Extension Installation")
    print("=" * 50)
    print(f"""
Install from Chrome Web Store:
  {CHROME_STORE_URL}

Or manually:
1. Open chrome://extensions/
2. Enable Developer mode
3. Click "Load unpacked"
4. Select: {get_install_dir() / "extension"}
""")


def main():
    print("=" * 60)
    print("       Tmura - Full Installation")
    print("=" * 60)
    install_dependencies()
    install_native_host()
    show_extension_instructions()
    print("\n" + "=" * 60)
    print("Installation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
