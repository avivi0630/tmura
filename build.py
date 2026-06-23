#!/usr/bin/env python3
"""
Tmura - Build Script v3.1
Compiles the application into a standalone executable using PyInstaller.
Prepares distribution folder for Inno Setup installer.
"""

import os
import sys
import subprocess
import shutil
import json
import platform
from pathlib import Path


def get_project_dir():
    return Path(__file__).parent.resolve()


def ensure_file(path: Path, create_default: bool = True):
    """Make sure a required file exists; create an empty default if missing."""
    if not path.exists() and create_default:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        print(f"Created empty placeholder: {path}")
    return path.exists()


def check_pyinstaller():
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True


def check_icon():
    project_dir = get_project_dir()
    icon_resources = project_dir / "app" / "resources" / "icon.ico"
    icon_root = project_dir / "icon.ico"

    if not icon_resources.exists() and not icon_root.exists():
        print("icon.ico not found, generating default...")
        gen = project_dir / "generate_icon.py"
        if gen.exists():
            subprocess.run([sys.executable, str(gen)], check=False)

    if icon_root.exists():
        if not icon_resources.exists():
            icon_resources.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(icon_root), str(icon_resources))
        return str(icon_root)

    if icon_resources.exists():
        shutil.copy2(str(icon_resources), str(icon_root))
        return str(icon_resources)

    print("WARNING: No icon.ico available. Building without icon.")
    return None


def prepare_dist_extra(dist_dir, project_dir, app_dir):
    """Prepare extra files in dist/ for the installer"""

    icon_root = project_dir / "icon.ico"
    if icon_root.exists():
        shutil.copy2(str(icon_root), str(dist_dir / "icon.ico"))
        print(f"Icon copied to: {dist_dir / 'icon.ico'}")

    ext_dir = project_dir / "extension"
    if ext_dir.exists():
        ext_dest = dist_dir / "extension"
        if ext_dest.exists():
            shutil.rmtree(ext_dest)
        shutil.copytree(ext_dir, ext_dest)
        print(f"Extension copied to: {ext_dest}")
    else:
        print("WARNING: extension/ folder not found - skipping.")

    req_file = project_dir / "requirements.txt"
    if req_file.exists():
        shutil.copy2(str(req_file), dist_dir / "requirements.txt")
    else:
        print("WARNING: requirements.txt not found - creating empty.")
        (dist_dir / "requirements.txt").write_text("", encoding="utf-8")

    host_dest = dist_dir / "app"
    host_dest.mkdir(exist_ok=True)

    for f in ["host.py", "install.py", "app_config.py", "translations.py", "native_host_setup.py"]:
        src = app_dir / f
        if src.exists():
            shutil.copy2(str(src), str(host_dest / f))
        else:
            print(f"WARNING: {f} not found in app/ - skipping.")

    manifest_path = host_dest / "com.compressor.host.json"
    manifest = {
        "name": "com.compressor.host",
        "description": "Tmura Native Host",
        "path": str(host_dest / "host_wrapper.bat"),
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://mefmiammilbcjogoclncpjcbpklgljal/"
        ]
    }
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest created: {manifest_path}")

    info_path = project_dir / "info_before.txt"
    if not info_path.exists():
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write("Tmura - Smart File Converter\n")
            f.write("=" * 40 + "\n\n")
            f.write("This will install Tmura on your computer.\n\n")
            f.write("Requirements:\n")
            f.write("- Python 3.11+ must be installed\n")
            f.write("- pip packages will be auto-installed on first run\n")
            f.write("- ffmpeg is recommended for video/audio conversion\n\n")
            f.write("Chrome Extension:\n")
            f.write("- After installation, the Chrome extension will be\n")
            f.write("  automatically registered for native messaging.\n")
            f.write("- Install the extension from the Chrome Web Store.\n")


def build_windows(icon_path=None):
    project_dir = get_project_dir()
    app_dir = project_dir / "app"
    dist_dir = project_dir / "dist"
    build_dir = project_dir / "build"

    for d in [dist_dir, build_dir]:
        if d.exists():
            shutil.rmtree(d)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Tmura",
        "--noconfirm",
        "--clean",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={build_dir}",
        "--windowed",
        "--onefile",
    ]

    # Add data files that actually exist
    data_files = [
        ("translations.py", "app"),
        ("app_config.py", "app"),
        ("host.py", "app"),
        ("install.py", "app"),
        ("native_host_setup.py", "app"),
        ("single_instance.py", "app"),
    ]
    for fname, dest in data_files:
        src = app_dir / fname
        if src.exists():
            cmd.append(f"--add-data={src}{os.pathsep}{dest}")
        else:
            print(f"WARNING: {src} not found - skipping data file.")

    if icon_path:
        cmd.append(f"--icon={icon_path}")
        cmd.append(f"--add-data={icon_path}{os.pathsep}.")

    hidden_imports = [
        "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "PIL", "PIL.Image", "PIL._tkinter_finder",
        "pillow_heif", "mutagen", "fitz",
        "single_instance", "ctypes.wintypes",
    ]
    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    cmd.append(str(app_dir / "gui_app.py"))

    print("Building Tmura.exe...")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = dist_dir / "Tmura.exe"
        if exe_path.exists():
            prepare_dist_extra(dist_dir, project_dir, app_dir)

            print("\n" + "=" * 60)
            print("BUILD SUCCESSFUL!")
            print(f"Executable: {exe_path}")
            print(f"Distribution folder: {dist_dir}")
            print("")
            print("To create installer:")
            print("  1. Install Inno Setup 6: https://jrsoftware.org/isdl.php")
            print("  2. Run: ISCC.exe setup.iss")
            print(f"  3. Installer will be in: installer_output/")
            print("=" * 60)
            return True

    print("BUILD FAILED!")
    return False


def build_macos(icon_path=None):
    project_dir = get_project_dir()
    app_dir = project_dir / "app"
    dist_dir = project_dir / "dist"
    build_dir = project_dir / "build"

    for d in [dist_dir, build_dir]:
        if d.exists():
            shutil.rmtree(d)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Tmura",
        "--noconfirm",
        "--clean",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={build_dir}",
        "--windowed",
        "--onefile",
    ]

    data_files = [
        ("translations.py", "app"),
        ("app_config.py", "app"),
        ("host.py", "app"),
        ("install.py", "app"),
        ("native_host_setup.py", "app"),
        ("single_instance.py", "app"),
    ]
    for fname, dest in data_files:
        src = app_dir / fname
        if src.exists():
            cmd.append(f"--add-data={src}:{dest}")
        else:
            print(f"WARNING: {src} not found - skipping data file.")

    if icon_path:
        cmd.append(f"--icon={icon_path}")
        cmd.append(f"--add-data={icon_path}:.")

    hidden_imports = [
        "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "PIL", "PIL.Image", "pillow_heif", "mutagen", "fitz",
        "single_instance", "ctypes.wintypes",
    ]
    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    cmd.append(str(app_dir / "gui_app.py"))

    print("Building Tmura for macOS...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = dist_dir / "Tmura"
        if exe_path.exists():
            if icon_path:
                shutil.copy2(icon_path, dist_dir / "icon.ico")
            ext_dir = project_dir / "extension"
            if ext_dir.exists():
                shutil.copytree(ext_dir, dist_dir / "extension")
            req_file = project_dir / "requirements.txt"
            if req_file.exists():
                shutil.copy2(str(req_file), dist_dir / "requirements.txt")

            host_dest = dist_dir / "app"
            host_dest.mkdir(exist_ok=True)
            for f in ["host.py", "install.py", "app_config.py", "translations.py", "native_host_setup.py"]:
                src = app_dir / f
                if src.exists():
                    shutil.copy2(str(src), str(host_dest / f))

            print(f"\nBUILD SUCCESSFUL! Executable: {exe_path}")
            return True

    print("BUILD FAILED!")
    return False


def build_linux(icon_path=None):
    project_dir = get_project_dir()
    app_dir = project_dir / "app"
    dist_dir = project_dir / "dist"
    build_dir = project_dir / "build"

    for d in [dist_dir, build_dir]:
        if d.exists():
            shutil.rmtree(d)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Tmura",
        "--noconfirm",
        "--clean",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={build_dir}",
        "--windowed",
        "--onefile",
    ]

    data_files = [
        ("translations.py", "app"),
        ("app_config.py", "app"),
        ("host.py", "app"),
        ("install.py", "app"),
        ("native_host_setup.py", "app"),
        ("single_instance.py", "app"),
    ]
    for fname, dest in data_files:
        src = app_dir / fname
        if src.exists():
            cmd.append(f"--add-data={src}:{dest}")
        else:
            print(f"WARNING: {src} not found - skipping data file.")

    if icon_path:
        cmd.append(f"--icon={icon_path}")
        cmd.append(f"--add-data={icon_path}:.")

    hidden_imports = [
        "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
        "PIL", "PIL.Image", "pillow_heif", "mutagen", "fitz",
        "single_instance", "ctypes.wintypes",
    ]
    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    cmd.append(str(app_dir / "gui_app.py"))

    print("Building Tmura for Linux...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = dist_dir / "Tmura"
        if exe_path.exists():
            if icon_path:
                shutil.copy2(icon_path, dist_dir / "icon.ico")
            ext_dir = project_dir / "extension"
            if ext_dir.exists():
                shutil.copytree(ext_dir, dist_dir / "extension")
            req_file = project_dir / "requirements.txt"
            if req_file.exists():
                shutil.copy2(str(req_file), dist_dir / "requirements.txt")

            host_dest = dist_dir / "app"
            host_dest.mkdir(exist_ok=True)
            for f in ["host.py", "install.py", "app_config.py", "translations.py", "native_host_setup.py"]:
                src = app_dir / f
                if src.exists():
                    shutil.copy2(str(src), str(host_dest / f))

            print(f"\nBUILD SUCCESSFUL! Executable: {exe_path}")
            return True

    print("BUILD FAILED!")
    return False


def main():
    print("=" * 60)
    print("       Tmura - Build Script v3.1")
    print("=" * 60)

    system = platform.system()
    print(f"Platform: {system}")

    check_pyinstaller()
    icon_path = check_icon()

    if system == "Windows":
        build_windows(icon_path)
    elif system == "Darwin":
        build_macos(icon_path)
    elif system == "Linux":
        build_linux(icon_path)
    else:
        print(f"Unsupported platform: {system}")


if __name__ == "__main__":
    main()
