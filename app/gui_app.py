#!/usr/bin/env python3
"""
Tmura - Smart File Converter GUI
Features:
- Single instance (no duplicates)
- Resolution-based image conversion
- Hidden ffmpeg console on Windows
- Audio metadata and cover art support
"""

import sys
import os
import subprocess
import json
import struct
import threading
import platform
import webbrowser
import shutil
from pathlib import Path
from typing import Optional, List, Dict

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)
    _meipass_app = os.path.join(sys._MEIPASS, 'app')
    if os.path.isdir(_meipass_app):
        sys.path.insert(0, _meipass_app)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QFileDialog, QComboBox,
    QProgressBar, QListWidget, QListWidgetItem, QCheckBox,
    QMessageBox, QGroupBox, QSlider, QLineEdit, QFrame,
    QSystemTrayIcon, QMenu, QStyle, QSizePolicy, QStackedWidget,
    QScrollArea, QDoubleSpinBox, QFormLayout, QTextEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QIcon, QFont, QColor, QAction, QPixmap

from translations import Translator, t, DEFAULT_LANG, LANG_HE, LANG_YI, LANG_EN
from app_config import AppConfig, get_install_dir, get_icon_path, HOST_NAME, EXTENSION_ID, CHROME_STORE_URL
from native_host_setup import is_native_host_installed, register_native_host, find_system_python

try:
    from PIL import Image
    _log_init = f"Pillow OK: {Image.__version__}"
except ImportError as _e:
    Image = None
    _log_init = f"Pillow MISSING: {_e}"

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pillow_heif = None

try:
    import fitz
except ImportError:
    fitz = None

try:
    import mutagen
    from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TRCK, TCON
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4, MP4Cover
    from mutagen.flac import FLAC, Picture
    from mutagen.oggvorbis import OggVorbis
except ImportError:
    mutagen = None
    APIC = TIT2 = TPE1 = TALB = TDRC = TRCK = TCON = None
    MP3 = MP4 = MP4Cover = FLAC = Picture = OggVorbis = None

APP_BRAND = "\u05EA\u05B0\u05BC\u05DE\u05D5\u05BC\u05E8\u05B8\u05D4"
APP_VERSION = "2.0"
SINGLE_INSTANCE_KEY = "TmuraSingleInstance"

# ==================== HIDDEN SUBPROCESS FOR FFMPEG ====================
def run_ffmpeg_hidden(cmd: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
    """Run ffmpeg without showing console window on Windows"""
    startupinfo = None
    creationflags = 0

    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW

    return subprocess.run(
        cmd,
        capture_output=True,
        timeout=timeout,
        startupinfo=startupinfo,
        creationflags=creationflags
    )


def _ffmpeg_bin() -> Optional[str]:
    return shutil.which("ffmpeg")


def _log(msg: str):
    if not hasattr(_log, 'entries'):
        _log.entries = []
    _log.entries.append(msg)
    print(msg)


def _init_log():
    _log(f"Python: {sys.executable}")
    _log(f"PIL: {_log_init}")
    _log(f"fitz (PyMuPDF): {'OK' if fitz else 'MISSING'}")
    _log(f"mutagen: {'OK' if mutagen else 'MISSING'}")
    _log(f"ffmpeg: {_ffmpeg_bin() or 'NOT FOUND'}")


# ==================== STYLES ====================
GLOBAL_STYLE = """
QMainWindow {
    background-color: #f5f5f7;
}
QScrollArea {
    border: none;
    background: transparent;
}
QTabWidget::pane {
    border: 1px solid #d2d2d7;
    border-radius: 12px;
    background-color: white;
    padding: 10px;
    top: -1px;
}
QTabWidget::tab-bar {
    alignment: center;
}
QTabBar::tab {
    background: #e5e5ea;
    color: #1d1d1f;
    padding: 10px 20px;
    margin: 2px 1px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    min-width: 60px;
}
QTabBar::tab:selected {
    background: #0071e3;
    color: white;
}
QTabBar::tab:hover:!selected {
    background: #d2d2d7;
}
QPushButton {
    background-color: #0071e3;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #0059c4;
}
QPushButton:pressed {
    background-color: #003d8f;
}
QPushButton:disabled {
    background-color: #c7c7cc;
    color: white;
}
QPushButton[secondary="true"] {
    background-color: #86868b;
}
QPushButton[secondary="true"]:hover {
    background-color: #636366;
}
QPushButton[success="true"] {
    background-color: #34c759;
}
QPushButton[success="true"]:hover {
    background-color: #2db84d;
}
QPushButton[danger="true"] {
    background-color: #ff3b30;
}
QPushButton[danger="true"]:hover {
    background-color: #d63028;
}
QPushButton[small="true"] {
    padding: 4px 10px;
    font-size: 11px;
    border-radius: 6px;
}
QComboBox {
    padding: 8px 14px;
    border: 2px solid #d2d2d7;
    border-radius: 10px;
    background: white;
    font-size: 13px;
    min-width: 160px;
}
QComboBox:hover {
    border-color: #0071e3;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    border: 2px solid #d2d2d7;
    border-radius: 10px;
    background: white;
    selection-background-color: #0071e3;
    selection-color: white;
    outline: none;
}
QListWidget {
    border: 2px dashed #d2d2d7;
    border-radius: 10px;
    background: #fafafa;
    padding: 6px;
    font-size: 13px;
}
QListWidget::item {
    padding: 6px 8px;
    border-radius: 6px;
    margin: 1px 0;
}
QListWidget::item:selected {
    background: #e5f0ff;
    color: #0071e3;
}
QProgressBar {
    border: none;
    border-radius: 6px;
    background: #e5e5ea;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: #34c759;
    border-radius: 6px;
}
QLabel {
    color: #1d1d1f;
    font-size: 13px;
}
QGroupBox {
    font-weight: 600;
    border: 2px solid #e5e5ea;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    padding-left: 12px;
    padding-right: 12px;
    padding-bottom: 12px;
    background: white;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #1d1d1f;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #e5e5ea;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #0071e3;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QCheckBox {
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 2px solid #d2d2d7;
}
QCheckBox::indicator:checked {
    background: #0071e3;
    border-color: #0071e3;
}
QLineEdit {
    padding: 8px 12px;
    border: 2px solid #d2d2d7;
    border-radius: 10px;
    background: white;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #0071e3;
}
QDoubleSpinBox {
    padding: 8px 12px;
    border: 2px solid #d2d2d7;
    border-radius: 10px;
    background: white;
    font-size: 13px;
}
QDoubleSpinBox:focus {
    border-color: #0071e3;
}
QSpinBox {
    padding: 8px 12px;
    border: 2px solid #d2d2d7;
    border-radius: 10px;
    background: white;
    font-size: 13px;
}
QSpinBox:focus {
    border-color: #0071e3;
}
QTextEdit {
    border: 2px solid #e5e5ea;
    border-radius: 8px;
    background: #fafafa;
    font-family: monospace;
    font-size: 11px;
    color: #636366;
    padding: 6px;
}
"""


# ==================== OUTPUT PATH HELPERS ====================
def get_output_dir_for_file(input_path: str, custom_dir: str = "") -> str:
    if custom_dir and os.path.isdir(custom_dir):
        return os.path.join(custom_dir, "קבצים שהומרו")
    parent = os.path.dirname(os.path.abspath(input_path))
    return os.path.join(parent, "קבצים שהומרו")


def get_output_path_for_file(input_path: str, output_format: str, custom_dir: str = "") -> str:
    name = Path(input_path).stem
    out_dir = get_output_dir_for_file(input_path, custom_dir)
    os.makedirs(out_dir, exist_ok=True)
    fmt = 'jpg' if output_format == 'jpeg' else output_format
    return os.path.join(out_dir, f"{name} - {APP_BRAND}.{fmt}")


# ==================== NATIVE HOST SETUP (delegates to native_host_setup) ====================
def setup_native_host():
    """Register the native host in a user-writable directory.
    Returns (success, localized_message). Does NOT write to Program Files."""
    success, payload = register_native_host()
    if success:
        return True, t("setup_success", path=payload)
    # payload is a prefixed error string
    if payload.startswith("PERMISSION:"):
        return False, t("setup_fail", error=t("setup_fail_permission") or payload)
    if payload.startswith("WRITE_FAIL:"):
        return False, t("setup_fail", error=t("setup_fail_write") or payload)
    if payload.startswith("REG_FAIL:"):
        return False, t("setup_fail", error=t("setup_fail_registry") or payload)
    return False, t("setup_fail", error=payload)


# ==================== CONVERSION WORKER ====================
class ConversionWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    file_processed = pyqtSignal(str, bool, str)

    def __init__(self, files: List[str], output_format: str, custom_dir: str = "",
                 quality: int = 80, options: Dict = None):
        super().__init__()
        self.files = files
        self.output_format = output_format.lower()
        self.custom_dir = custom_dir
        self.quality = quality
        self.options = options or {}
        self._is_cancelled = False

    def run(self):
        errors = []
        try:
            total = len(self.files)
            success_count = 0
            for i, file_path in enumerate(self.files):
                if self._is_cancelled:
                    break
                self.progress.emit(
                    int((i / total) * 100),
                    t("converting_file", file=os.path.basename(file_path))
                )
                try:
                    result, err = self.convert_file(file_path)
                    if result:
                        success_count += 1
                    else:
                        errors.append(f"{os.path.basename(file_path)}: {err}")
                    self.file_processed.emit(file_path, result, err)
                except Exception as e:
                    err = str(e)
                    errors.append(f"{os.path.basename(file_path)}: {err}")
                    _log(f"Error converting {file_path}: {e}")
                    self.file_processed.emit(file_path, False, err)

            self.progress.emit(100, t("done"))
            msg = t("converted_count", success=success_count, total=total)
            if errors:
                msg += "\n\n" + t("conversion_errors") + ":\n" + "\n".join(errors)
            self.finished.emit(success_count > 0, msg)
        except Exception as e:
            self.finished.emit(False, str(e))

    def convert_file(self, file_path: str):
        ext = Path(file_path).suffix.lower()
        output_path = get_output_path_for_file(file_path, self.output_format, self.custom_dir)
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.bmp', '.tiff', '.tif', '.gif', '.ico']:
            return self.convert_image(file_path, output_path)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.flv', '.m4v', '.gif']:
            return self.convert_video(file_path, output_path)
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma']:
            return self.convert_audio(file_path, output_path)
        elif ext == '.pdf':
            return self.convert_pdf(file_path, output_path)
        return False, t("error_unsupported_format")

    def convert_image(self, input_path: str, output_path: str):
        if not Image:
            return False, t("error_no_library", lib="Pillow")
        try:
            img = Image.open(input_path)

            target_width = self.options.get('target_width', 0)
            target_height = self.options.get('target_height', 0)
            if target_width > 0 or target_height > 0:
                orig_w, orig_h = img.size
                if target_width > 0 and target_height > 0:
                    img = img.resize((target_width, target_height), Image.LANCZOS)
                elif target_width > 0:
                    ratio = target_width / orig_w
                    new_h = int(orig_h * ratio)
                    img = img.resize((target_width, new_h), Image.LANCZOS)
                elif target_height > 0:
                    ratio = target_height / orig_h
                    new_w = int(orig_w * ratio)
                    img = img.resize((new_w, target_height), Image.LANCZOS)

            fmt = self.output_format
            if fmt in ['jpg', 'jpeg']:
                if img.mode in ['RGBA', 'LA', 'P']:
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ['RGBA', 'LA'] else None)
                    img = background
                save_kwargs = {'format': 'JPEG', 'quality': self.quality, 'optimize': True}
            elif fmt == 'png':
                save_kwargs = {'format': 'PNG', 'optimize': True}
            elif fmt == 'webp':
                save_kwargs = {'format': 'WEBP', 'quality': self.quality}
            elif fmt == 'gif':
                save_kwargs = {'format': 'GIF'}
            elif fmt == 'bmp':
                save_kwargs = {'format': 'BMP'}
            elif fmt == 'tiff':
                save_kwargs = {'format': 'TIFF'}
            elif fmt == 'ico':
                sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
                img_sizes = []
                for s in sizes:
                    resized = img.resize(s, Image.LANCZOS)
                    if resized.mode == 'RGBA':
                        img_sizes.append(resized)
                    else:
                        rgba = resized.convert('RGBA')
                        img_sizes.append(rgba)
                img_sizes[0].save(output_path, format='ICO', append_images=img_sizes[1:])
                return True, ""
            elif fmt == 'heic':
                save_kwargs = {'format': 'HEIF'}
            else:
                save_kwargs = {'format': fmt.upper()}
            img.save(output_path, **save_kwargs)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True, ""
            return False, t("error_output_empty")
        except Exception as e:
            err = str(e)
            _log(f"Image conversion error: {err}")
            return False, err

    def convert_video(self, input_path: str, output_path: str):
        ffmpeg_bin = _ffmpeg_bin()
        if not ffmpeg_bin:
            return False, t("error_no_library", lib="ffmpeg")
        try:
            threads = self.options.get('threads', 0)
            thread_args = ['-threads', str(threads)] if threads and threads > 0 else []
            if self.output_format == 'gif':
                cmd = [ffmpeg_bin, '-y', '-i', input_path] + thread_args + [
                    '-vf', f'fps=10,scale=480:-1:flags=lanczos', output_path]
                result = run_ffmpeg_hidden(cmd, timeout=300)
            elif self.output_format == 'ico':
                cmd = [ffmpeg_bin, '-y', '-i', input_path] + thread_args + [
                    '-vf', 'scale=256:256', '-frames:v', '1', output_path]
                result = run_ffmpeg_hidden(cmd, timeout=300)
            else:
                codec_map = {'mp4': 'libx264', 'webm': 'libvpx-vp9', 'avi': 'mpeg4',
                             'mkv': 'libx264', 'mov': 'libx264'}
                audio_map = {'mp4': 'aac', 'webm': 'libvorbis', 'avi': 'mp3',
                             'mkv': 'aac', 'mov': 'aac'}
                codec = codec_map.get(self.output_format, 'libx264')
                acodec = audio_map.get(self.output_format, 'aac')
                crf = int(51 - (self.quality / 100) * 36)
                cmd = [ffmpeg_bin, '-y', '-i', input_path] + thread_args + [
                    '-vcodec', codec, '-acodec', acodec, '-crf', str(crf),
                    output_path]
                result = run_ffmpeg_hidden(cmd, timeout=300)
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True, ""
            stderr = result.stderr.decode(errors='replace')[-500:]
            _log(f"ffmpeg failed (rc={result.returncode}): {stderr}")
            return False, f"ffmpeg: {stderr[:200]}"
        except subprocess.TimeoutExpired:
            return False, t("error_timeout")
        except Exception as e:
            return False, str(e)

    def convert_audio(self, input_path: str, output_path: str):
        ffmpeg_bin = _ffmpeg_bin()
        if not ffmpeg_bin:
            return False, t("error_no_library", lib="ffmpeg")
        try:
            codec_map = {'mp3': 'libmp3lame', 'aac': 'aac', 'wav': 'pcm_s16le',
                         'flac': 'flac', 'ogg': 'libvorbis', 'm4a': 'aac'}
            codec = codec_map.get(self.output_format, 'libmp3lame')
            cmd = [ffmpeg_bin, '-y', '-i', input_path, '-acodec', codec]
            if codec == 'libmp3lame':
                br = f"{int(self.quality * 3.2)}k"
                cmd.extend(['-b:a', br])
            if self.output_format == 'm4a':
                cmd.extend(['-f', 'mp4', '-strict', '-2'])
            if self.output_format == 'aac':
                cmd.extend(['-f', 'adts'])
            if self.options.get('threads'):
                cmd.extend(['-threads', str(self.options['threads'])])
            cmd.append(output_path)
            _log(f"Audio cmd: {' '.join(cmd)}")
            result = run_ffmpeg_hidden(cmd, timeout=300)
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True, ""
            stderr = result.stderr.decode(errors='replace')[-500:]
            _log(f"ffmpeg audio failed (rc={result.returncode}): {stderr}")
            return False, f"ffmpeg: {stderr[:200]}"
        except subprocess.TimeoutExpired:
            return False, t("error_timeout")
        except Exception as e:
            return False, str(e)

    def convert_pdf(self, input_path: str, output_path: str):
        try:
            if self.output_format in ['jpg', 'jpeg', 'png'] and fitz:
                doc = fitz.open(input_path)
                for i, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=150)
                    fmt = 'jpg' if self.output_format in ['jpg', 'jpeg'] else self.output_format
                    img_path = output_path.rsplit('.', 1)[0] + f"_page{i+1}.{fmt}"
                    pix.save(img_path)
                doc.close()
                return True, ""
            elif self.output_format == 'txt' and fitz:
                doc = fitz.open(input_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                doc.close()
                return True, ""
            if not fitz:
                return False, t("error_no_library", lib="PyMuPDF")
            return False, t("error_unsupported_format")
        except Exception as e:
            return False, str(e)

    def cancel(self):
        self._is_cancelled = True


# ==================== PDF MERGE WORKER ====================
class PdfMergeWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, files: List[str], output_path: str):
        super().__init__()
        self.files = files
        self.output_path = output_path

    def run(self):
        try:
            if not fitz:
                self.finished.emit(False, t("error_no_library", lib="PyMuPDF"))
                return
            merged = fitz.open()
            total = len(self.files)
            for i, f in enumerate(self.files):
                self.progress.emit(int((i / total) * 100), os.path.basename(f))
                doc = fitz.open(f)
                merged.insert_pdf(doc)
                doc.close()
            self.progress.emit(100, t("done"))
            merged.save(self.output_path)
            merged.close()
            self.finished.emit(True, t("merge_success", path=self.output_path))
        except Exception as e:
            self.finished.emit(False, str(e))


# ==================== PDF CROP MARKS WORKER ====================
class PdfCropMarksWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, files: List[str], crop_cm: float, custom_dir: str = ""):
        super().__init__()
        self.files = files
        self.crop_cm = crop_cm
        self.custom_dir = custom_dir

    def run(self):
        try:
            if not fitz:
                self.finished.emit(False, t("error_no_library", lib="PyMuPDF"))
                return
            total = len(self.files)
            success = 0
            for i, f in enumerate(self.files):
                self.progress.emit(int((i / total) * 100), os.path.basename(f))
                out_dir = get_output_dir_for_file(f, self.custom_dir)
                os.makedirs(out_dir, exist_ok=True)
                name = Path(f).stem
                out_path = os.path.join(out_dir, f"{name} - {APP_BRAND}_cropmarks.pdf")
                doc = fitz.open(f)
                out_doc = fitz.open()
                cm_to_pt = 28.3465
                margin = self.crop_cm * cm_to_pt
                for page in doc:
                    rect = page.rect
                    new_w = rect.width + 2 * margin
                    new_h = rect.height + 2 * margin
                    new_page = out_doc.new_page(width=new_w, height=new_h)
                    new_page.show_pdf_page(
                        fitz.Rect(margin, margin, margin + rect.width, margin + rect.height),
                        doc, page.number
                    )
                    mark_len = min(margin * 0.6, 20)
                    color = (0.5, 0.5, 0.5)
                    lw = 0.5
                    corners = [
                        fitz.Point(margin, margin),
                        fitz.Point(margin + rect.width, margin),
                        fitz.Point(margin, margin + rect.height),
                        fitz.Point(margin + rect.width, margin + rect.height),
                    ]
                    for c in corners:
                        new_page.draw_line(fitz.Point(c.x - mark_len, c.y),
                                           fitz.Point(c.x + mark_len, c.y), color=color, width=lw)
                        new_page.draw_line(fitz.Point(c.x, c.y - mark_len),
                                           fitz.Point(c.x, c.y + mark_len), color=color, width=lw)
                out_doc.save(out_path)
                out_doc.close()
                doc.close()
                success += 1
            self.progress.emit(100, t("done"))
            self.finished.emit(True, t("converted_count", success=success, total=total))
        except Exception as e:
            self.finished.emit(False, str(e))


# ==================== AUDIO METADATA HELPERS ====================
def read_audio_metadata(file_path: str) -> Dict:
    meta = {"title": "", "artist": "", "album": "", "year": "", "track": "", "genre": "", "has_cover": False}
    if not mutagen:
        return meta
    try:
        ext = Path(file_path).suffix.lower()
        if ext == '.mp3':
            mp3 = MP3(file_path)
            tags = mp3.tags
            if tags:
                meta["title"] = str(tags.get("TIT2", ""))
                meta["artist"] = str(tags.get("TPE1", ""))
                meta["album"] = str(tags.get("TALB", ""))
                meta["year"] = str(tags.get("TDRC", ""))
                meta["track"] = str(tags.get("TRCK", ""))
                meta["genre"] = str(tags.get("TCON", ""))
                meta["has_cover"] = any(isinstance(f, APIC) or (hasattr(f, 'data') and isinstance(getattr(f, 'data', None), bytes)) for f in tags.getall("APIC"))
        elif ext in ['.m4a', '.mp4']:
            mp4 = MP4(file_path)
            tags = mp4.tags
            if tags:
                meta["title"] = str(tags.get("\xa9nam", [""])[0])
                meta["artist"] = str(tags.get("\xa9ART", [""])[0])
                meta["album"] = str(tags.get("\xa9alb", [""])[0])
                meta["year"] = str(tags.get("\xa9day", [""])[0])
                meta["track"] = str(tags.get("trkn", [(0,0)])[0][0]) if tags.get("trkn") else ""
                meta["genre"] = str(tags.get("\xa9gen", [""])[0])
                meta["has_cover"] = bool(tags.get("covr"))
        elif ext == '.flac':
            flac = FLAC(file_path)
            meta["title"] = flac.get("title", [""])[0]
            meta["artist"] = flac.get("artist", [""])[0]
            meta["album"] = flac.get("album", [""])[0]
            meta["year"] = flac.get("date", [""])[0]
            meta["track"] = flac.get("tracknumber", [""])[0]
            meta["genre"] = flac.get("genre", [""])[0]
            meta["has_cover"] = len(flac.pictures) > 0
        elif ext == '.ogg':
            ogg = OggVorbis(file_path)
            meta["title"] = ogg.get("title", [""])[0]
            meta["artist"] = ogg.get("artist", [""])[0]
            meta["album"] = ogg.get("album", [""])[0]
            meta["year"] = ogg.get("date", [""])[0]
            meta["track"] = ogg.get("tracknumber", [""])[0]
            meta["genre"] = ogg.get("genre", [""])[0]
    except Exception as e:
        _log(f"Error reading metadata: {e}")
    return meta


def write_audio_metadata(file_path: str, meta: Dict) -> bool:
    if not mutagen:
        return False
    try:
        ext = Path(file_path).suffix.lower()
        if ext == '.mp3':
            mp3 = MP3(file_path)
            if mp3.tags is None:
                mp3.add_tags()
            tags = mp3.tags
            if meta.get("title"):
                tags.add(TIT2(encoding=3, text=meta["title"]))
            if meta.get("artist"):
                tags.add(TPE1(encoding=3, text=meta["artist"]))
            if meta.get("album"):
                tags.add(TALB(encoding=3, text=meta["album"]))
            if meta.get("year"):
                tags.add(TDRC(encoding=3, text=meta["year"]))
            if meta.get("track"):
                tags.add(TRCK(encoding=3, text=meta["track"]))
            if meta.get("genre"):
                tags.add(TCON(encoding=3, text=meta["genre"]))
            mp3.save()
            return True
        elif ext in ['.m4a', '.mp4']:
            mp4 = MP4(file_path)
            if mp4.tags is None:
                mp4.add_tags()
            tags = mp4.tags
            if meta.get("title"):
                tags["\xa9nam"] = [meta["title"]]
            if meta.get("artist"):
                tags["\xa9ART"] = [meta["artist"]]
            if meta.get("album"):
                tags["\xa9alb"] = [meta["album"]]
            if meta.get("year"):
                tags["\xa9day"] = [meta["year"]]
            if meta.get("track"):
                tags["trkn"] = [(int(meta["track"]), 0)]
            if meta.get("genre"):
                tags["\xa9gen"] = [meta["genre"]]
            mp4.save()
            return True
        elif ext == '.flac':
            flac = FLAC(file_path)
            if meta.get("title"):
                flac["title"] = [meta["title"]]
            if meta.get("artist"):
                flac["artist"] = [meta["artist"]]
            if meta.get("album"):
                flac["album"] = [meta["album"]]
            if meta.get("year"):
                flac["date"] = [meta["year"]]
            if meta.get("track"):
                flac["tracknumber"] = [meta["track"]]
            if meta.get("genre"):
                flac["genre"] = [meta["genre"]]
            flac.save()
            return True
        elif ext == '.ogg':
            ogg = OggVorbis(file_path)
            if meta.get("title"):
                ogg["title"] = [meta["title"]]
            if meta.get("artist"):
                ogg["artist"] = [meta["artist"]]
            if meta.get("album"):
                ogg["album"] = [meta["album"]]
            if meta.get("year"):
                ogg["date"] = [meta["year"]]
            if meta.get("track"):
                ogg["tracknumber"] = [meta["track"]]
            if meta.get("genre"):
                ogg["genre"] = [meta["genre"]]
            ogg.save()
            return True
        return False
    except Exception as e:
        _log(f"Error writing metadata: {e}")
        return False


def extract_cover_art(file_path: str, output_path: str) -> bool:
    if not mutagen:
        return False
    try:
        ext = Path(file_path).suffix.lower()
        if ext == '.mp3':
            mp3 = MP3(file_path)
            if mp3.tags:
                for frame in mp3.tags.getall("APIC"):
                    with open(output_path, 'wb') as f:
                        f.write(frame.data)
                    return True
        elif ext in ['.m4a', '.mp4']:
            mp4 = MP4(file_path)
            if mp4.tags and mp4.tags.get("covr"):
                cover = mp4.tags["covr"][0]
                with open(output_path, 'wb') as f:
                    f.write(bytes(cover))
                return True
        elif ext == '.flac':
            flac = FLAC(file_path)
            if flac.pictures:
                with open(output_path, 'wb') as f:
                    f.write(flac.pictures[0].data)
                return True
        return False
    except Exception as e:
        _log(f"Error extracting cover: {e}")
        return False


def set_cover_art(file_path: str, image_path: str) -> bool:
    if not mutagen:
        return False
    try:
        ext = Path(file_path).suffix.lower()
        with open(image_path, 'rb') as f:
            img_data = f.read()
        img_ext = Path(image_path).suffix.lower()
        mime = "image/jpeg" if img_ext in ['.jpg', '.jpeg'] else "image/png"

        if ext == '.mp3':
            mp3 = MP3(file_path)
            if mp3.tags is None:
                mp3.add_tags()
            mp3.tags.delall("APIC")
            mp3.tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=img_data))
            mp3.save()
            return True
        elif ext in ['.m4a', '.mp4']:
            mp4 = MP4(file_path)
            if mp4.tags is None:
                mp4.add_tags()
            img_format = MP4Cover.FORMAT_JPEG if mime == "image/jpeg" else MP4Cover.FORMAT_PNG
            mp4.tags["covr"] = [MP4Cover(img_data, imageformat=img_format)]
            mp4.save()
            return True
        elif ext == '.flac':
            flac = FLAC(file_path)
            flac.clear_pictures()
            pic = Picture()
            pic.type = 3
            pic.mime = mime
            pic.data = img_data
            flac.add_picture(pic)
            flac.save()
            return True
        return False
    except Exception as e:
        _log(f"Error setting cover: {e}")
        return False


def wrap_in_scroll(widget: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    return scroll


# ==================== FILE LIST WITH THUMBNAILS ====================
class ThumbListWidget(QListWidget):
    """List widget that shows thumbnail previews of files"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(64, 64))
        self.setGridSize(QSize(80, 80))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setMovement(QListWidget.Movement.Static)
        self.setWordWrap(True)

    def add_file(self, file_path: str):
        item = QListWidgetItem()
        item.setToolTip(file_path)
        item.setText(os.path.basename(file_path))
        ext = Path(file_path).suffix.lower()
        pixmap = self._load_thumb(file_path, ext)
        if pixmap and not pixmap.isNull():
            item.setIcon(QIcon(pixmap))
        self.addItem(item)

    def _load_thumb(self, file_path: str, ext: str) -> Optional[QPixmap]:
        try:
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.bmp', '.tiff', '.tif', '.gif', '.ico']:
                if Image:
                    img = Image.open(file_path)
                    img.thumbnail((64, 64))
                    if img.mode in ['RGBA', 'LA', 'P']:
                        img = img.convert('RGBA')
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    import io
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    png_data = buf.getvalue()
                    from PyQt6.QtGui import QImage
                    qimg = QImage.fromData(png_data)
                    if not qimg.isNull():
                        return QPixmap.fromImage(qimg)
                else:
                    pm = QPixmap(file_path)
                    if not pm.isNull():
                        return pm.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            elif ext == '.pdf' and fitz:
                doc = fitz.open(file_path)
                if len(doc) > 0:
                    page = doc[0]
                    pix = page.get_pixmap(dpi=20)
                    img_data = pix.tobytes("png")
                    qimg = None
                    from PyQt6.QtGui import QImage
                    qimg = QImage.fromData(img_data)
                    doc.close()
                    return QPixmap.fromImage(qimg)
                doc.close()
            elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma']:
                if mutagen:
                    import tempfile
                    tmp = os.path.join(tempfile.gettempdir(), "tmura_thumb.jpg")
                    if extract_cover_art(file_path, tmp):
                        pm = QPixmap(tmp)
                        try:
                            os.unlink(tmp)
                        except Exception:
                            pass
                        if not pm.isNull():
                            return pm.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.flv', '.m4v']:
                ffmpeg_bin = _ffmpeg_bin()
                if ffmpeg_bin:
                    import tempfile
                    tmp = os.path.join(tempfile.gettempdir(), "tmura_vthumb.jpg")
                    cmd = [ffmpeg_bin, '-y', '-i', file_path, '-vf',
                           'scale=64:-1', '-frames:v', '1', tmp]
                    run_ffmpeg_hidden(cmd, timeout=5)
                    if os.path.exists(tmp):
                        pm = QPixmap(tmp)
                        try:
                            os.unlink(tmp)
                        except Exception:
                            pass
                        if not pm.isNull():
                            return pm
        except Exception as e:
            _log(f"Thumb error for {file_path}: {e}")
        return None


# ==================== CONVERTER TAB ====================
class ConverterTab(QWidget):
    def __init__(self, media_type: str, formats: List[str], parent=None):
        super().__init__(parent)
        self.media_type = media_type
        self.formats = formats
        self.files: List[str] = []
        self.worker = None
        self.setup_ui()
        Translator.instance().add_observer(self._on_language_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.files_group = QGroupBox(t("files_to_convert"))
        files_layout = QVBoxLayout(self.files_group)
        files_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton(t("add_files"))
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton(t("remove_selected"))
        self.remove_btn.setProperty("danger", True)
        self.remove_btn.setProperty("small", True)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton(t("clear"))
        self.clear_btn.setProperty("secondary", True)
        self.clear_btn.setProperty("small", True)
        self.clear_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(self.add_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.clear_btn)
        files_layout.addLayout(btn_row)

        self.file_list = ThumbListWidget()
        self.file_list.setMinimumHeight(140)
        files_layout.addWidget(self.file_list)

        self.count_label = QLabel(t("files_count", count=0))
        self.count_label.setStyleSheet("color: #86868b; font-size: 12px;")
        files_layout.addWidget(self.count_label)

        layout.addWidget(self.files_group)

        self.settings_group = QGroupBox(t("settings"))
        settings_layout = QVBoxLayout(self.settings_group)
        settings_layout.setSpacing(10)

        fmt_row = QHBoxLayout()
        self.fmt_label = QLabel(t("output_format"))
        fmt_row.addWidget(self.fmt_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.formats)
        fmt_row.addWidget(self.format_combo)
        fmt_row.addStretch()
        settings_layout.addLayout(fmt_row)

        if self.media_type == "Image":
            res_group = QGroupBox(t("resolution_settings"))
            res_layout = QVBoxLayout(res_group)
            res_layout.setSpacing(8)

            self.keep_original_size_cb = QCheckBox(t("keep_original_size"))
            self.keep_original_size_cb.setChecked(True)
            res_layout.addWidget(self.keep_original_size_cb)

            dim_row = QHBoxLayout()
            self.width_label = QLabel(t("width"))
            dim_row.addWidget(self.width_label)
            self.width_spin = QSpinBox()
            self.width_spin.setRange(0, 10000)
            self.width_spin.setValue(0)
            self.width_spin.setSpecialValueText(t("auto"))
            self.width_spin.setEnabled(False)
            dim_row.addWidget(self.width_spin)

            self.height_label = QLabel(t("height"))
            dim_row.addWidget(self.height_label)
            self.height_spin = QSpinBox()
            self.height_spin.setRange(0, 10000)
            self.height_spin.setValue(0)
            self.height_spin.setSpecialValueText(t("auto"))
            self.height_spin.setEnabled(False)
            dim_row.addWidget(self.height_spin)
            dim_row.addStretch()
            res_layout.addLayout(dim_row)

            self.keep_original_size_cb.stateChanged.connect(
                lambda s: (self.width_spin.setEnabled(s != Qt.CheckState.Checked.value),
                           self.height_spin.setEnabled(s != Qt.CheckState.Checked.value)))

            settings_layout.addWidget(res_group)

        qual_row = QHBoxLayout()
        self.qual_label = QLabel(t("quality"))
        qual_row.addWidget(self.qual_label)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(AppConfig.instance().get("last_quality", 80))
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        qual_row.addWidget(self.quality_slider)
        self.quality_label = QLabel(f"{self.quality_slider.value()}%")
        self.quality_label.setMinimumWidth(45)
        self.quality_label.setStyleSheet("font-weight: 600; color: #0071e3;")
        qual_row.addWidget(self.quality_label)
        qual_row.addStretch()
        settings_layout.addLayout(qual_row)

        out_row = QHBoxLayout()
        self.out_label = QLabel(t("output_folder"))
        out_row.addWidget(self.out_label)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(t("output_auto_hint"))
        out_row.addWidget(self.output_edit)
        self.browse_btn = QPushButton(t("browse"))
        self.browse_btn.setProperty("secondary", True)
        self.browse_btn.clicked.connect(self.browse_output)
        out_row.addWidget(self.browse_btn)
        settings_layout.addLayout(out_row)

        self.auto_folder_info = QLabel(t("auto_folder_info"))
        self.auto_folder_info.setStyleSheet("color: #86868b; font-size: 11px;")
        self.auto_folder_info.setWordWrap(True)
        settings_layout.addWidget(self.auto_folder_info)

        if self.media_type in ("Video", "Audio"):
            import multiprocessing
            max_threads = multiprocessing.cpu_count() or 8
            thread_row = QHBoxLayout()
            self.thread_label = QLabel(t("cpu_threads"))
            thread_row.addWidget(self.thread_label)
            self.thread_slider = QSlider(Qt.Orientation.Horizontal)
            self.thread_slider.setRange(1, max_threads)
            self.thread_slider.setValue(max_threads)
            thread_row.addWidget(self.thread_slider)
            self.thread_val_label = QLabel(str(max_threads))
            self.thread_val_label.setMinimumWidth(30)
            self.thread_val_label.setStyleSheet("font-weight: 600; color: #0071e3;")
            thread_row.addWidget(self.thread_val_label)
            self.thread_slider.valueChanged.connect(
                lambda v: self.thread_val_label.setText(str(v)))
            thread_row.addStretch()
            settings_layout.addLayout(thread_row)

        layout.addWidget(self.settings_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #86868b; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.convert_btn = QPushButton(t("convert"))
        self.convert_btn.setMinimumHeight(44)
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)

        layout.addStretch()

    def _on_language_changed(self):
        self.files_group.setTitle(t("files_to_convert"))
        self.add_btn.setText(t("add_files"))
        self.remove_btn.setText(t("remove_selected"))
        self.clear_btn.setText(t("clear"))
        self.settings_group.setTitle(t("settings"))
        self.fmt_label.setText(t("output_format"))
        self.qual_label.setText(t("quality"))
        self.out_label.setText(t("output_folder"))
        self.browse_btn.setText(t("browse"))
        self.convert_btn.setText(t("convert"))
        self.count_label.setText(t("files_count", count=len(self.files)))
        self.output_edit.setPlaceholderText(t("output_auto_hint"))
        self.auto_folder_info.setText(t("auto_folder_info"))
        if hasattr(self, 'keep_original_size_cb'):
            self.keep_original_size_cb.setText(t("keep_original_size"))
            self.width_label.setText(t("width"))
            self.height_label.setText(t("height"))
        if not self.worker or not self.worker.isRunning():
            self.convert_btn.setText(t("convert"))

    def update_quality_label(self, val):
        self.quality_label.setText(f"{val}%")
        AppConfig.instance().set("last_quality", val)

    def add_files(self):
        filters = {
            "Image": "Images (*.jpg *.jpeg *.png *.webp *.heic *.heif *.bmp *.tiff *.tif *.gif *.ico)",
            "Video": "Videos (*.mp4 *.avi *.mov *.mkv *.webm *.wmv *.flv *.m4v)",
            "Audio": "Audio (*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma)",
            "PDF": "Documents (*.pdf)"
        }
        files, _ = QFileDialog.getOpenFileNames(
            self, t("select_files"), "", filters.get(self.media_type, "All Files (*)")
        )
        if files:
            self.files.extend(files)
            self.update_file_list()

    def remove_selected(self):
        selected = self.file_list.selectedItems()
        if not selected:
            return
        to_remove = set()
        for item in selected:
            path = item.toolTip()
            to_remove.add(path)
        self.files = [f for f in self.files if f not in to_remove]
        self.update_file_list()

    def clear_files(self):
        self.files.clear()
        self.update_file_list()

    def update_file_list(self):
        self.file_list.clear()
        for f in self.files:
            self.file_list.add_file(f)
        self.count_label.setText(t("files_count", count=len(self.files)))

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, t("select_output_folder"))
        if folder:
            self.output_edit.setText(folder)

    def start_conversion(self):
        if not self.files:
            QMessageBox.warning(self, t("error"), t("error_no_files"))
            return
        custom_dir = self.output_edit.text().strip()
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText(t("converting"))
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        options = {}
        if hasattr(self, 'thread_slider'):
            options['threads'] = self.thread_slider.value()

        if self.media_type == "Image" and hasattr(self, 'keep_original_size_cb'):
            if not self.keep_original_size_cb.isChecked():
                options['target_width'] = self.width_spin.value() if self.width_spin.value() > 0 else 0
                options['target_height'] = self.height_spin.value() if self.height_spin.value() > 0 else 0

        self.worker = ConversionWorker(
            self.files.copy(), self.format_combo.currentText(),
            custom_dir, self.quality_slider.value(), options
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.file_processed.connect(self.on_file_processed)
        self.worker.start()

    def on_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def on_file_processed(self, file_path, success, err):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.toolTip() == file_path:
                item.setForeground(QColor("#34c759") if success else QColor("#ff3b30"))
                break

    def on_finished(self, success, msg):
        self.status_label.setText(msg)
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText(t("convert"))
        self.progress_bar.setVisible(False)
        if success:
            QMessageBox.information(self, t("success"), msg)
        else:
            QMessageBox.warning(self, t("error"), msg)


# ==================== AUDIO TAB ====================
class AudioTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files: List[str] = []
        self.convert_worker = None
        self.setup_ui()
        Translator.instance().add_observer(self._on_language_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.files_group = QGroupBox(t("files_to_convert"))
        files_layout = QVBoxLayout(self.files_group)
        files_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton(t("add_files"))
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton(t("remove_selected"))
        self.remove_btn.setProperty("danger", True)
        self.remove_btn.setProperty("small", True)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton(t("clear"))
        self.clear_btn.setProperty("secondary", True)
        self.clear_btn.setProperty("small", True)
        self.clear_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(self.add_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.clear_btn)
        files_layout.addLayout(btn_row)

        self.file_list = ThumbListWidget()
        self.file_list.setMinimumHeight(100)
        self.file_list.currentRowChanged.connect(self._on_file_selected)
        files_layout.addWidget(self.file_list)

        self.count_label = QLabel(t("files_count", count=0))
        self.count_label.setStyleSheet("color: #86868b; font-size: 12px;")
        files_layout.addWidget(self.count_label)

        layout.addWidget(self.files_group)

        self.convert_group = QGroupBox(t("audio_convert"))
        convert_layout = QVBoxLayout(self.convert_group)
        convert_layout.setSpacing(10)

        fmt_row = QHBoxLayout()
        self.fmt_label = QLabel(t("output_format"))
        fmt_row.addWidget(self.fmt_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "wav", "flac", "aac", "ogg", "m4a"])
        fmt_row.addWidget(self.format_combo)
        fmt_row.addStretch()
        convert_layout.addLayout(fmt_row)

        qual_row = QHBoxLayout()
        self.qual_label = QLabel(t("quality"))
        qual_row.addWidget(self.qual_label)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(AppConfig.instance().get("last_quality", 80))
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        qual_row.addWidget(self.quality_slider)
        self.quality_label = QLabel(f"{self.quality_slider.value()}%")
        self.quality_label.setMinimumWidth(45)
        self.quality_label.setStyleSheet("font-weight: 600; color: #0071e3;")
        qual_row.addWidget(self.quality_label)
        qual_row.addStretch()
        convert_layout.addLayout(qual_row)

        import multiprocessing
        max_threads = multiprocessing.cpu_count() or 8
        thread_row = QHBoxLayout()
        self.thread_label = QLabel(t("cpu_threads"))
        thread_row.addWidget(self.thread_label)
        self.thread_slider = QSlider(Qt.Orientation.Horizontal)
        self.thread_slider.setRange(1, max_threads)
        self.thread_slider.setValue(max_threads)
        thread_row.addWidget(self.thread_slider)
        self.thread_val_label = QLabel(str(max_threads))
        self.thread_val_label.setMinimumWidth(30)
        self.thread_val_label.setStyleSheet("font-weight: 600; color: #0071e3;")
        thread_row.addWidget(self.thread_val_label)
        self.thread_slider.valueChanged.connect(
            lambda v: self.thread_val_label.setText(str(v)))
        thread_row.addStretch()
        convert_layout.addLayout(thread_row)

        self.convert_btn = QPushButton(t("convert"))
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.clicked.connect(self.start_convert)
        convert_layout.addWidget(self.convert_btn)

        layout.addWidget(self.convert_group)

        self.cover_group = QGroupBox(t("audio_cover"))
        cover_layout = QVBoxLayout(self.cover_group)
        cover_layout.setSpacing(10)

        cover_row = QHBoxLayout()
        self.cover_preview = QLabel()
        self.cover_preview.setFixedSize(100, 100)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setStyleSheet(
            "border: 2px dashed #d2d2d7; border-radius: 8px; background: #fafafa; color: #86868b; font-size: 11px;"
        )
        self.cover_preview.setText(t("no_cover"))
        cover_row.addWidget(self.cover_preview)

        cover_btns = QVBoxLayout()
        self.extract_cover_btn = QPushButton(t("extract_cover"))
        self.extract_cover_btn.setProperty("secondary", True)
        self.extract_cover_btn.clicked.connect(self.extract_cover)
        cover_btns.addWidget(self.extract_cover_btn)

        self.add_cover_btn = QPushButton(t("add_cover"))
        self.add_cover_btn.setProperty("success", True)
        self.add_cover_btn.clicked.connect(self.add_cover)
        cover_btns.addWidget(self.add_cover_btn)

        cover_row.addLayout(cover_btns)
        cover_layout.addLayout(cover_row)

        layout.addWidget(self.cover_group)

        self.meta_group = QGroupBox(t("audio_metadata"))
        meta_form = QFormLayout(self.meta_group)
        meta_form.setSpacing(8)

        self.title_edit = QLineEdit()
        meta_form.addRow(t("meta_title"), self.title_edit)
        self.artist_edit = QLineEdit()
        meta_form.addRow(t("meta_artist"), self.artist_edit)
        self.album_edit = QLineEdit()
        meta_form.addRow(t("meta_album"), self.album_edit)
        self.year_edit = QLineEdit()
        meta_form.addRow(t("meta_year"), self.year_edit)
        self.track_edit = QLineEdit()
        meta_form.addRow(t("meta_track"), self.track_edit)
        self.genre_edit = QLineEdit()
        meta_form.addRow(t("meta_genre"), self.genre_edit)

        self.save_meta_btn = QPushButton(t("save_metadata"))
        self.save_meta_btn.setMinimumHeight(40)
        self.save_meta_btn.clicked.connect(self.save_metadata)
        meta_form.addRow(self.save_meta_btn)

        layout.addWidget(self.meta_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #86868b; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _on_language_changed(self):
        self.files_group.setTitle(t("files_to_convert"))
        self.add_btn.setText(t("add_files"))
        self.remove_btn.setText(t("remove_selected"))
        self.clear_btn.setText(t("clear"))
        self.count_label.setText(t("files_count", count=len(self.files)))
        self.convert_group.setTitle(t("audio_convert"))
        self.fmt_label.setText(t("output_format"))
        self.qual_label.setText(t("quality"))
        self.convert_btn.setText(t("convert"))
        self.cover_group.setTitle(t("audio_cover"))
        self.extract_cover_btn.setText(t("extract_cover"))
        self.add_cover_btn.setText(t("add_cover"))
        self.meta_group.setTitle(t("audio_metadata"))

    def update_quality_label(self, val):
        self.quality_label.setText(f"{val}%")
        AppConfig.instance().set("last_quality", val)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, t("select_files"), "", "Audio (*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma)"
        )
        if files:
            self.files.extend(files)
            self.update_file_list()

    def remove_selected(self):
        selected = self.file_list.selectedItems()
        if not selected:
            return
        to_remove = set()
        for item in selected:
            to_remove.add(item.toolTip())
        self.files = [f for f in self.files if f not in to_remove]
        self.update_file_list()

    def clear_files(self):
        self.files.clear()
        self.update_file_list()

    def update_file_list(self):
        self.file_list.clear()
        for f in self.files:
            self.file_list.add_file(f)
        self.count_label.setText(t("files_count", count=len(self.files)))

    def _get_selected_file(self) -> Optional[str]:
        items = self.file_list.selectedItems()
        if not items:
            return None
        return items[0].toolTip()

    def _on_file_selected(self, row):
        file_path = self._get_selected_file()
        if not file_path:
            return
        meta = read_audio_metadata(file_path)
        self.title_edit.setText(meta.get("title", ""))
        self.artist_edit.setText(meta.get("artist", ""))
        self.album_edit.setText(meta.get("album", ""))
        self.year_edit.setText(meta.get("year", ""))
        self.track_edit.setText(meta.get("track", ""))
        self.genre_edit.setText(meta.get("genre", ""))
        self.cover_preview.clear()
        if meta.get("has_cover"):
            try:
                import tempfile
                tmp = os.path.join(tempfile.gettempdir(), "tmura_cover_preview.jpg")
                if extract_cover_art(file_path, tmp):
                    pixmap = QPixmap(tmp)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                               Qt.TransformationMode.SmoothTransformation)
                        self.cover_preview.setPixmap(scaled)
                    try:
                        os.unlink(tmp)
                    except Exception:
                        pass
                    return
            except Exception:
                pass
        self.cover_preview.setText(t("no_cover"))

    def start_convert(self):
        if not self.files:
            QMessageBox.warning(self, t("error"), t("error_no_files"))
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText(t("converting"))
        options = {}
        if hasattr(self, 'thread_slider'):
            options['threads'] = self.thread_slider.value()
        self.convert_worker = ConversionWorker(
            self.files.copy(), self.format_combo.currentText(),
            "", self.quality_slider.value(), options
        )
        self.convert_worker.progress.connect(self.on_progress)
        self.convert_worker.finished.connect(self.on_convert_finished)
        self.convert_worker.file_processed.connect(self.on_file_processed)
        self.convert_worker.start()

    def extract_cover(self):
        file_path = self._get_selected_file()
        if not file_path:
            QMessageBox.warning(self, t("error"), t("error_select_file"))
            return
        out_dir = get_output_dir_for_file(file_path)
        os.makedirs(out_dir, exist_ok=True)
        name = Path(file_path).stem
        out_path = os.path.join(out_dir, f"{name} - {APP_BRAND}_cover.jpg")
        if extract_cover_art(file_path, out_path):
            QMessageBox.information(self, t("success"), t("cover_extracted", path=out_path))
            pixmap = QPixmap(out_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
                self.cover_preview.setPixmap(scaled)
        else:
            QMessageBox.warning(self, t("error"), t("error_no_cover"))

    def add_cover(self):
        file_path = self._get_selected_file()
        if not file_path:
            QMessageBox.warning(self, t("error"), t("error_select_file"))
            return
        img_path, _ = QFileDialog.getOpenFileName(
            self, t("select_cover_image"), "",
            "Images (*.jpg *.jpeg *.png)"
        )
        if not img_path:
            return
        if set_cover_art(file_path, img_path):
            QMessageBox.information(self, t("success"), t("cover_added"))
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
                self.cover_preview.setPixmap(scaled)
        else:
            QMessageBox.warning(self, t("error"), t("error_cover_add"))

    def save_metadata(self):
        file_path = self._get_selected_file()
        if not file_path:
            QMessageBox.warning(self, t("error"), t("error_select_file"))
            return
        meta = {
            "title": self.title_edit.text().strip(),
            "artist": self.artist_edit.text().strip(),
            "album": self.album_edit.text().strip(),
            "year": self.year_edit.text().strip(),
            "track": self.track_edit.text().strip(),
            "genre": self.genre_edit.text().strip(),
        }
        if write_audio_metadata(file_path, meta):
            QMessageBox.information(self, t("success"), t("metadata_saved"))
        else:
            QMessageBox.warning(self, t("error"), t("error_metadata_save"))

    def on_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def on_file_processed(self, file_path, success, err):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.toolTip() == file_path:
                item.setForeground(QColor("#34c759") if success else QColor("#ff3b30"))
                break

    def on_convert_finished(self, success, msg):
        self.progress_bar.setVisible(False)
        self.status_label.setText(msg)
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText(t("convert"))
        if success:
            QMessageBox.information(self, t("success"), msg)
        else:
            QMessageBox.warning(self, t("error"), msg)


# ==================== PDF TAB ====================
class PdfTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files: List[str] = []
        self.convert_worker = None
        self.merge_worker = None
        self.crop_worker = None
        self.setup_ui()
        Translator.instance().add_observer(self._on_language_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.files_group = QGroupBox(t("files_to_convert"))
        files_layout = QVBoxLayout(self.files_group)
        files_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton(t("add_files"))
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton(t("remove_selected"))
        self.remove_btn.setProperty("danger", True)
        self.remove_btn.setProperty("small", True)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton(t("clear"))
        self.clear_btn.setProperty("secondary", True)
        self.clear_btn.setProperty("small", True)
        self.clear_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(self.add_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.clear_btn)
        files_layout.addLayout(btn_row)

        self.file_list = ThumbListWidget()
        self.file_list.setMinimumHeight(120)
        files_layout.addWidget(self.file_list)

        self.count_label = QLabel(t("files_count", count=0))
        self.count_label.setStyleSheet("color: #86868b; font-size: 12px;")
        files_layout.addWidget(self.count_label)

        layout.addWidget(self.files_group)

        self.convert_group = QGroupBox(t("pdf_convert"))
        convert_layout = QVBoxLayout(self.convert_group)
        convert_layout.setSpacing(10)

        fmt_row = QHBoxLayout()
        self.fmt_label = QLabel(t("output_format"))
        fmt_row.addWidget(self.fmt_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["txt", "jpg", "png"])
        fmt_row.addWidget(self.format_combo)
        fmt_row.addStretch()
        convert_layout.addLayout(fmt_row)

        self.convert_btn = QPushButton(t("convert"))
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.clicked.connect(self.start_convert)
        convert_layout.addWidget(self.convert_btn)

        layout.addWidget(self.convert_group)

        self.merge_group = QGroupBox(t("pdf_merge"))
        merge_layout = QVBoxLayout(self.merge_group)
        merge_layout.setSpacing(10)

        self.merge_info = QLabel(t("merge_info"))
        self.merge_info.setStyleSheet("color: #86868b; font-size: 12px;")
        self.merge_info.setWordWrap(True)
        merge_layout.addWidget(self.merge_info)

        self.merge_btn = QPushButton(t("merge_btn"))
        self.merge_btn.setProperty("success", True)
        self.merge_btn.setMinimumHeight(40)
        self.merge_btn.clicked.connect(self.start_merge)
        merge_layout.addWidget(self.merge_btn)

        layout.addWidget(self.merge_group)

        self.crop_group = QGroupBox(t("pdf_crop_marks"))
        crop_layout = QVBoxLayout(self.crop_group)
        crop_layout.setSpacing(10)

        crop_row = QHBoxLayout()
        self.crop_label = QLabel(t("crop_margin_cm"))
        crop_row.addWidget(self.crop_label)
        self.crop_spin = QDoubleSpinBox()
        self.crop_spin.setRange(0.5, 20.0)
        self.crop_spin.setValue(1.0)
        self.crop_spin.setSingleStep(0.5)
        self.crop_spin.setSuffix(" cm")
        crop_row.addWidget(self.crop_spin)
        crop_row.addStretch()
        crop_layout.addLayout(crop_row)

        self.crop_info = QLabel(t("crop_info"))
        self.crop_info.setStyleSheet("color: #86868b; font-size: 11px;")
        self.crop_info.setWordWrap(True)
        crop_layout.addWidget(self.crop_info)

        self.crop_btn = QPushButton(t("add_crop_marks"))
        self.crop_btn.setProperty("secondary", True)
        self.crop_btn.setMinimumHeight(40)
        self.crop_btn.clicked.connect(self.start_crop_marks)
        crop_layout.addWidget(self.crop_btn)

        layout.addWidget(self.crop_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #86868b; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _on_language_changed(self):
        self.files_group.setTitle(t("files_to_convert"))
        self.add_btn.setText(t("add_files"))
        self.remove_btn.setText(t("remove_selected"))
        self.clear_btn.setText(t("clear"))
        self.count_label.setText(t("files_count", count=len(self.files)))
        self.convert_group.setTitle(t("pdf_convert"))
        self.fmt_label.setText(t("output_format"))
        self.convert_btn.setText(t("convert"))
        self.merge_group.setTitle(t("pdf_merge"))
        self.merge_info.setText(t("merge_info"))
        self.merge_btn.setText(t("merge_btn"))
        self.crop_group.setTitle(t("pdf_crop_marks"))
        self.crop_label.setText(t("crop_margin_cm"))
        self.crop_info.setText(t("crop_info"))
        self.crop_btn.setText(t("add_crop_marks"))

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, t("select_files"), "", "Documents (*.pdf)"
        )
        if files:
            self.files.extend(files)
            self.update_file_list()

    def remove_selected(self):
        selected = self.file_list.selectedItems()
        if not selected:
            return
        to_remove = set()
        for item in selected:
            to_remove.add(item.toolTip())
        self.files = [f for f in self.files if f not in to_remove]
        self.update_file_list()

    def clear_files(self):
        self.files.clear()
        self.update_file_list()

    def update_file_list(self):
        self.file_list.clear()
        for f in self.files:
            self.file_list.add_file(f)
        self.count_label.setText(t("files_count", count=len(self.files)))

    def _show_progress(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

    def _hide_progress(self):
        self.progress_bar.setVisible(False)

    def start_convert(self):
        if not self.files:
            QMessageBox.warning(self, t("error"), t("error_no_files"))
            return
        self._show_progress()
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText(t("converting"))
        self.convert_worker = ConversionWorker(
            self.files.copy(), self.format_combo.currentText(), "", 80
        )
        self.convert_worker.progress.connect(self.on_progress)
        self.convert_worker.finished.connect(self.on_convert_finished)
        self.convert_worker.file_processed.connect(self.on_file_processed)
        self.convert_worker.start()

    def start_merge(self):
        if len(self.files) < 2:
            QMessageBox.warning(self, t("error"), t("error_merge_min"))
            return
        first_file = self.files[0]
        out_dir = get_output_dir_for_file(first_file)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"merged - {APP_BRAND}.pdf")
        self._show_progress()
        self.merge_btn.setEnabled(False)
        self.merge_worker = PdfMergeWorker(self.files.copy(), out_path)
        self.merge_worker.progress.connect(self.on_progress)
        self.merge_worker.finished.connect(self.on_merge_finished)
        self.merge_worker.start()

    def start_crop_marks(self):
        if not self.files:
            QMessageBox.warning(self, t("error"), t("error_no_files"))
            return
        self._show_progress()
        self.crop_btn.setEnabled(False)
        self.crop_worker = PdfCropMarksWorker(self.files.copy(), self.crop_spin.value())
        self.crop_worker.progress.connect(self.on_progress)
        self.crop_worker.finished.connect(self.on_crop_finished)
        self.crop_worker.start()

    def on_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def on_file_processed(self, file_path, success, err):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.toolTip() == file_path:
                item.setForeground(QColor("#34c759") if success else QColor("#ff3b30"))
                break

    def on_convert_finished(self, success, msg):
        self._hide_progress()
        self.status_label.setText(msg)
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText(t("convert"))
        if success:
            QMessageBox.information(self, t("success"), msg)
        else:
            QMessageBox.warning(self, t("error"), msg)

    def on_merge_finished(self, success, msg):
        self._hide_progress()
        self.status_label.setText(msg)
        self.merge_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, t("success"), msg)
        else:
            QMessageBox.warning(self, t("error"), msg)

    def on_crop_finished(self, success, msg):
        self._hide_progress()
        self.status_label.setText(msg)
        self.crop_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, t("success"), msg)
        else:
            QMessageBox.warning(self, t("error"), msg)


# ==================== EXTENSION TAB ====================
class ExtensionTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        Translator.instance().add_observer(self._on_language_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.ext_group = QGroupBox(t("extension_title"))
        ext_layout = QVBoxLayout(self.ext_group)
        ext_layout.setSpacing(10)

        self.desc_label = QLabel(t("extension_desc"))
        self.desc_label.setStyleSheet("color: #86868b; font-size: 13px; line-height: 1.6;")
        self.desc_label.setWordWrap(True)
        ext_layout.addWidget(self.desc_label)

        id_row = QHBoxLayout()
        self.id_label_text = QLabel(t("extension_id"))
        id_row.addWidget(self.id_label_text)
        id_val = QLabel(EXTENSION_ID)
        id_val.setStyleSheet("color: #0071e3; font-weight: 600; font-size: 12px;")
        id_val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        id_row.addWidget(id_val)
        id_row.addStretch()
        ext_layout.addLayout(id_row)

        self.install_btn = QPushButton(t("install_from_store"))
        self.install_btn.setMinimumHeight(42)
        self.install_btn.setProperty("success", True)
        self.install_btn.clicked.connect(self._open_store)
        ext_layout.addWidget(self.install_btn)

        layout.addWidget(self.ext_group)

        self.host_group = QGroupBox(t("native_host_title"))
        host_layout = QVBoxLayout(self.host_group)
        host_layout.setSpacing(10)

        status_row = QHBoxLayout()
        self.status_label_text = QLabel(t("connection_status"))
        status_row.addWidget(self.status_label_text)
        self.host_status = QLabel(t("checking"))
        self.host_status.setStyleSheet("font-weight: 600;")
        status_row.addWidget(self.host_status)
        status_row.addStretch()
        host_layout.addLayout(status_row)

        self.setup_btn = QPushButton(t("setup_native_host"))
        self.setup_btn.setMinimumHeight(42)
        self.setup_btn.clicked.connect(self._setup_host)
        host_layout.addWidget(self.setup_btn)

        self.check_btn = QPushButton(t("check_connection"))
        self.check_btn.setProperty("secondary", True)
        self.check_btn.clicked.connect(self._check_connection)
        host_layout.addWidget(self.check_btn)

        layout.addWidget(self.host_group)

        self.how_group = QGroupBox(t("how_it_works"))
        how_layout = QVBoxLayout(self.how_group)
        how_layout.setSpacing(4)
        self.step_labels = []
        for key in ["step1", "step2", "step3", "step4", "step5"]:
            lbl = QLabel(t(key))
            lbl.setStyleSheet("font-size: 13px; padding: 2px 0;")
            lbl.setWordWrap(True)
            how_layout.addWidget(lbl)
            self.step_labels.append(lbl)

        layout.addWidget(self.how_group)
        layout.addStretch()

        QTimer.singleShot(100, self._refresh_status)

    def _on_language_changed(self):
        self.ext_group.setTitle(t("extension_title"))
        self.desc_label.setText(t("extension_desc"))
        self.id_label_text.setText(t("extension_id"))
        self.install_btn.setText(t("install_from_store"))
        self.host_group.setTitle(t("native_host_title"))
        self.status_label_text.setText(t("connection_status"))
        self.setup_btn.setText(t("reinstall_native_host") if is_native_host_installed() else t("setup_native_host"))
        self.check_btn.setText(t("check_connection"))
        self.how_group.setTitle(t("how_it_works"))
        for i, key in enumerate(["step1", "step2", "step3", "step4", "step5"]):
            self.step_labels[i].setText(t(key))

    def _open_store(self):
        webbrowser.open(CHROME_STORE_URL)

    def _refresh_status(self):
        installed = is_native_host_installed()
        if installed:
            self.host_status.setText(t("connected"))
            self.host_status.setStyleSheet("color: #34c759; font-weight: 600;")
            self.setup_btn.setText(t("reinstall_native_host"))
        else:
            self.host_status.setText(t("not_connected"))
            self.host_status.setStyleSheet("color: #ff3b30; font-weight: 600;")
            self.setup_btn.setText(t("setup_native_host"))

    def _setup_host(self):
        try:
            success, message = setup_native_host()
        except Exception as e:
            success = False
            message = t("setup_fail", error=str(e))
        if success:
            QMessageBox.information(self, t("success"), message)
        else:
            QMessageBox.warning(self, t("error"), message)
        self._refresh_status()

    def _check_connection(self):
        try:
            install_dir = get_install_dir()
            host_path = install_dir / "app" / "host.py"
            if not host_path.exists():
                meipass = getattr(sys, "_MEIPASS", None)
                if meipass and (Path(meipass) / "app" / "host.py").exists():
                    host_path = Path(meipass) / "app" / "host.py"
            python_exe = find_system_python()
            ping_msg = json.dumps({"action": "ping"}).encode('utf-8')
            length = struct.pack('I', len(ping_msg))
            result = subprocess.run(
                [python_exe, str(host_path)],
                input=length + ping_msg, capture_output=True, timeout=5
            )
            if result.returncode == 0 and result.stdout:
                resp_len = struct.unpack('I', result.stdout[:4])[0]
                resp = json.loads(result.stdout[4:4+resp_len].decode('utf-8'))
                if resp.get('success'):
                    self.host_status.setText(t("connected_responding"))
                    self.host_status.setStyleSheet("color: #34c759; font-weight: 600;")
                    QMessageBox.information(self, t("success"), t("host_connection_ok"))
                else:
                    self.host_status.setText(t("error_in_response"))
                    self.host_status.setStyleSheet("color: #ff9500; font-weight: 600;")
            else:
                self.host_status.setText(t("host_not_responding"))
                self.host_status.setStyleSheet("color: #ff3b30; font-weight: 600;")
                QMessageBox.warning(self, t("error"), t("host_check_fail"))
        except subprocess.TimeoutExpired:
            self.host_status.setText(t("host_timeout"))
            self.host_status.setStyleSheet("color: #ff3b30; font-weight: 600;")
            QMessageBox.warning(self, t("error"), t("host_check_timeout"))
        except Exception as e:
            self.host_status.setText(t("connection_error"))
            self.host_status.setStyleSheet("color: #ff3b30; font-weight: 600;")
            QMessageBox.warning(self, t("error"), t("host_check_error", error=str(e)))


# ==================== SETTINGS TAB ====================
class SettingsTab(QWidget):
    auto_start_changed = pyqtSignal(bool)
    background_server_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        Translator.instance().add_observer(self._on_language_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.app_group = QGroupBox(t("app_settings"))
        app_layout = QVBoxLayout(self.app_group)
        app_layout.setSpacing(10)

        lang_row = QHBoxLayout()
        self.lang_label = QLabel(t("language"))
        lang_row.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem(t("lang_hebrew"), LANG_HE)
        self.lang_combo.addItem(t("lang_yiddish"), LANG_YI)
        self.lang_combo.addItem(t("lang_english"), LANG_EN)
        current = AppConfig.instance().language
        idx = self.lang_combo.findData(current)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        app_layout.addLayout(lang_row)

        status_row = QHBoxLayout()
        self.server_label = QLabel(t("server_status"))
        status_row.addWidget(self.server_label)
        self.server_status = QLabel(t("server_not_active"))
        self.server_status.setStyleSheet("color: #ff3b30; font-weight: 600;")
        status_row.addWidget(self.server_status)
        status_row.addStretch()
        app_layout.addLayout(status_row)

        self.bg_server_cb = QCheckBox(t("background_server"))
        self.bg_server_cb.setChecked(AppConfig.instance().background_server)
        self.bg_server_cb.stateChanged.connect(self._on_bg_server_changed)
        app_layout.addWidget(self.bg_server_cb)

        self.auto_start_cb = QCheckBox(t("start_with_windows"))
        self.auto_start_cb.setChecked(AppConfig.instance().get("start_with_windows", False))
        self.auto_start_cb.stateChanged.connect(self._on_auto_start_changed)
        app_layout.addWidget(self.auto_start_cb)

        self.min_tray_cb = QCheckBox(t("minimize_to_tray"))
        self.min_tray_cb.setChecked(AppConfig.instance().minimize_to_tray)
        self.min_tray_cb.stateChanged.connect(self._on_min_tray_changed)
        app_layout.addWidget(self.min_tray_cb)

        layout.addWidget(self.app_group)

        self.shortcuts_group = QGroupBox(t("shortcuts"))
        shortcuts_layout = QVBoxLayout(self.shortcuts_group)
        self.shortcut_rows = []
        for key, desc_key in [("Ctrl+O", "shortcut_add"), ("Ctrl+M", "shortcut_convert"),
                              ("Ctrl+W", "shortcut_close"), ("Ctrl+Q", "shortcut_quit")]:
            row = QHBoxLayout()
            key_lbl = QLabel(key)
            key_lbl.setStyleSheet("font-weight: 600; font-family: monospace;")
            row.addWidget(key_lbl)
            row.addStretch()
            desc_lbl = QLabel(t(desc_key))
            row.addWidget(desc_lbl)
            shortcuts_layout.addLayout(row)
            self.shortcut_rows.append((key, desc_key, key_lbl, desc_lbl))

        layout.addWidget(self.shortcuts_group)

        self.log_group = QGroupBox(t("error_log"))
        log_layout = QVBoxLayout(self.log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        log_layout.addWidget(self.log_text)
        self.refresh_log_btn = QPushButton(t("refresh_log"))
        self.refresh_log_btn.setProperty("secondary", True)
        self.refresh_log_btn.clicked.connect(self._refresh_log)
        log_layout.addWidget(self.refresh_log_btn)
        layout.addWidget(self.log_group)

        layout.addStretch()

    def _on_language_changed(self):
        self.app_group.setTitle(t("app_settings"))
        self.lang_label.setText(t("language"))
        self.server_label.setText(t("server_status"))
        self.bg_server_cb.setText(t("background_server"))
        self.auto_start_cb.setText(t("start_with_windows"))
        self.min_tray_cb.setText(t("minimize_to_tray"))
        self.shortcuts_group.setTitle(t("shortcuts"))
        self.lang_combo.setItemText(0, t("lang_hebrew"))
        self.lang_combo.setItemText(1, t("lang_yiddish"))
        self.lang_combo.setItemText(2, t("lang_english"))
        for key, desc_key, key_lbl, desc_lbl in self.shortcut_rows:
            desc_lbl.setText(t(desc_key))
        if AppConfig.instance().background_server:
            self.server_status.setText(t("server_active"))
        else:
            self.server_status.setText(t("server_not_active"))
        self.log_group.setTitle(t("error_log"))
        self.refresh_log_btn.setText(t("refresh_log"))

    def _refresh_log(self):
        entries = getattr(_log, 'entries', [])
        self.log_text.setText("\n".join(entries[-100:]))

    def _on_lang_changed(self, idx):
        lang = self.lang_combo.itemData(idx)
        if lang:
            AppConfig.instance().language = lang
            Translator.instance().lang = lang
            app = QApplication.instance()
            if lang in (LANG_HE, LANG_YI):
                app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            else:
                app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def _on_auto_start_changed(self, state):
        enabled = state == Qt.CheckState.Checked.value
        AppConfig.instance().set("start_with_windows", enabled)
        if platform.system() == "Windows":
            self._set_windows_auto_start(enabled)
        self.auto_start_changed.emit(enabled)

    def _on_min_tray_changed(self, state):
        AppConfig.instance().minimize_to_tray = (state == Qt.CheckState.Checked.value)

    def _on_bg_server_changed(self, state):
        enabled = state == Qt.CheckState.Checked.value
        AppConfig.instance().background_server = enabled
        self.background_server_changed.emit(enabled)
        if enabled:
            self.server_status.setText(t("server_active"))
            self.server_status.setStyleSheet("color: #34c759; font-weight: 600;")
        else:
            self.server_status.setText(t("server_not_active"))
            self.server_status.setStyleSheet("color: #ff3b30; font-weight: 600;")

    def _set_windows_auto_start(self, enable: bool):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
            if enable:
                exe_path = sys.executable
                winreg.SetValueEx(key, "Tmura", 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, "Tmura")
                except Exception:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error setting auto start: {e}")


# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        config = AppConfig.instance()
        tr = Translator.instance()
        tr.lang = config.language

        self.setWindowTitle(f"{t('app_title')} v{APP_VERSION}")
        self.setMinimumSize(680, 520)
        self.resize(720, 560)

        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self.setup_tray()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.header = QLabel(t("app_name"))
        header_font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        self.header.setFont(header_font)
        self.header.setStyleSheet(
            "background: #0071e3; color: white; padding: 16px 20px; "
            "border-bottom: 2px solid #0059c4;"
        )
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header.setMinimumHeight(60)
        layout.addWidget(self.header)

        self.tabs = QTabWidget()

        self.image_tab = ConverterTab("Image", ["jpg", "jpeg", "png", "webp", "gif", "heic", "tiff", "bmp", "ico"])
        self.tabs.addTab(wrap_in_scroll(self.image_tab), t("tab_images"))

        self.video_tab = ConverterTab("Video", ["mp4", "webm", "avi", "mkv", "mov", "gif", "ico"])
        self.tabs.addTab(wrap_in_scroll(self.video_tab), t("tab_video"))

        self.audio_tab = AudioTab()
        self.tabs.addTab(wrap_in_scroll(self.audio_tab), t("tab_audio"))

        self.pdf_tab = PdfTab()
        self.tabs.addTab(wrap_in_scroll(self.pdf_tab), t("tab_pdf"))

        self.extension_tab = ExtensionTab()
        self.tabs.addTab(wrap_in_scroll(self.extension_tab), t("tab_extension"))

        self.settings_tab = SettingsTab()
        self.settings_tab.auto_start_changed.connect(self._on_auto_start)
        self.settings_tab.background_server_changed.connect(self._on_bg_server)
        self.settings_tab.min_tray_cb.stateChanged.connect(
            lambda s: setattr(self, 'close_to_tray', s == Qt.CheckState.Checked.value)
        )
        self.tabs.addTab(wrap_in_scroll(self.settings_tab), t("tab_settings"))

        layout.addWidget(self.tabs)

        self.setStyleSheet(GLOBAL_STYLE)
        self.close_to_tray = config.minimize_to_tray

        if config.language in (LANG_HE, LANG_YI):
            QApplication.instance().setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        tr.add_observer(self._on_language_changed)

    def _on_language_changed(self):
        self.setWindowTitle(f"{t('app_title')} v{APP_VERSION}")
        self.header.setText(t("app_name"))
        self.tabs.setTabText(0, t("tab_images"))
        self.tabs.setTabText(1, t("tab_video"))
        self.tabs.setTabText(2, t("tab_audio"))
        self.tabs.setTabText(3, t("tab_pdf"))
        self.tabs.setTabText(4, t("tab_extension"))
        self.tabs.setTabText(5, t("tab_settings"))

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = get_icon_path()
        if icon_path:
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        tray_menu = QMenu()
        show_action = QAction(t("tray_show"), self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction(t("tray_quit"), self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
            self.setWindowState(
                (self.windowState() & ~Qt.WindowState.WindowMinimized)
                | Qt.WindowState.WindowActive
            )
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click: toggle visibility
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()

    def _on_auto_start(self, enabled):
        pass

    def _on_bg_server(self, enabled):
        if enabled:
            self._start_background_server()
        else:
            self._stop_background_server()

    def _start_background_server(self):
        try:
            from app_config import get_install_dir
            install_dir = get_install_dir()
            host_path = install_dir / "app" / "host.py"
            if not host_path.exists():
                meipass = getattr(sys, "_MEIPASS", None)
                if meipass and (Path(meipass) / "app" / "host.py").exists():
                    host_path = Path(meipass) / "app" / "host.py"
            self._bg_process = subprocess.Popen(
                [find_system_python(), str(host_path)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
        except Exception as e:
            print(f"Error starting background server: {e}")

    def _stop_background_server(self):
        if hasattr(self, '_bg_process') and self._bg_process:
            try:
                self._bg_process.terminate()
                self._bg_process.wait(timeout=3)
            except Exception:
                try:
                    self._bg_process.kill()
                except Exception:
                    pass
            self._bg_process = None

    def closeEvent(self, event):
        if self.close_to_tray:
            event.ignore()
            self.hide()
        else:
            self.quit_app()

    def quit_app(self):
        self._stop_background_server()
        QApplication.quit()


def main():
    import os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from single_instance import check_single_instance, signal_existing_instance, register_show_window_callback

    # Check single-instance FIRST, before any heavy initialization.
    # If another instance is running, signal it to show its window and exit.
    if not check_single_instance():
        signal_existing_instance()
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("Tmura")
    app.setQuitOnLastWindowClosed(False)

    _init_log()

    window = MainWindow()
    register_show_window_callback(window)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
