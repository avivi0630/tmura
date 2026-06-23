#!/usr/bin/env python3
"""
Tmura - Native Messaging Host v3.0
Supports image compression and video conversion
"""

import sys
import json
import struct
import os
import base64
import logging
import platform
import subprocess
import shutil
import tempfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

if platform.system() == "Windows":
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

OUTPUT_DIR_NAME = "קבצים שהומרו"
APP_BRAND = "תמורה"


def setup_pil():
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        logger.info("HEIC/HEIF support enabled")
        return True
    except ImportError:
        logger.warning("pillow-heif not installed")
        return False


def get_output_dir():
    desktop = Path.home() / "Desktop"
    out_dir = desktop / OUTPUT_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir)


def run_ffmpeg_hidden(cmd, timeout=300):
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


def compress_image(msg):
    from PIL import Image
    from io import BytesIO

    if not msg.get('fileBase64') or not msg.get('quality'):
        return {"success": False, "error": "Missing parameters"}

    try:
        try:
            data = base64.b64decode(msg['fileBase64'])
        except Exception:
            return {"success": False, "error": "Invalid Base64 data"}

        img = Image.open(BytesIO(data))
        original_size = len(data)

        max_width = 2560
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.Resampling.BILINEAR)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        quality_map = {"low": 15, "medium": 35, "high": 70}
        quality = quality_map.get(msg['quality'], 50)

        output = BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        compressed_data = output.getvalue()
        compressed_b64 = base64.b64encode(compressed_data).decode('utf-8')
        ratio = round((1 - len(compressed_data) / original_size) * 100, 1)

        logger.info(f"Compressed: {original_size} -> {len(compressed_data)} ({ratio}% reduction)")
        return {
            "success": True,
            "fileBase64": compressed_b64,
            "format": "JPEG",
            "originalSize": original_size,
            "compressedSize": len(compressed_data),
            "compressionRatio": ratio
        }
    except Exception as e:
        logger.error(f"Compression error: {e}")
        return {"success": False, "error": f"Compression failed: {e}"}


def convert_video(msg):
    """Convert video file sent as base64 and save to output folder"""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return {"success": False, "error": "ffmpeg not found on system"}

    if not msg.get('fileBase64'):
        return {"success": False, "error": "Missing file data"}

    try:
        data = base64.b64decode(msg['fileBase64'])
        fmt = msg.get('format', 'mp4')
        if fmt not in ['mp4', 'webm', 'mkv', 'avi', 'mov']:
            fmt = 'mp4'

        tmp_in = os.path.join(tempfile.gettempdir(), f"tmura_input_{os.getpid()}.tmp")
        with open(tmp_in, 'wb') as f:
            f.write(data)

        out_dir = get_output_dir()
        out_path = os.path.join(out_dir, f"video - {APP_BRAND}.{fmt}")

        quality_map = {"low": 40, "medium": 28, "high": 18}
        crf = quality_map.get(msg.get('quality', 'medium'), 28)

        cmd = [ffmpeg_bin, '-y', '-i', tmp_in, '-vcodec', 'libx264',
               '-acodec', 'aac', '-crf', str(crf), out_path]
        result = run_ffmpeg_hidden(cmd, timeout=120)

        try:
            os.unlink(tmp_in)
        except Exception:
            pass

        if result.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            logger.info(f"Video converted: {out_path}")
            if platform.system() == "Windows":
                subprocess.run(['explorer', out_dir], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            elif platform.system() == "Darwin":
                subprocess.run(['open', out_dir], capture_output=True)
            else:
                subprocess.run(['xdg-open', out_dir], capture_output=True)
            return {"success": True, "path": out_path, "format": fmt}
        else:
            stderr = result.stderr.decode(errors='replace')[-300:]
            logger.error(f"Video conversion failed: {stderr}")
            return {"success": False, "error": f"ffmpeg error: {stderr[:150]}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Video conversion timed out"}
    except Exception as e:
        logger.error(f"Video conversion error: {e}")
        return {"success": False, "error": str(e)}


def save_image_to_folder(msg):
    """Save compressed image to output folder (instead of clipboard)"""
    from PIL import Image
    from io import BytesIO

    if not msg.get('fileBase64') or not msg.get('quality'):
        return {"success": False, "error": "Missing parameters"}

    try:
        data = base64.b64decode(msg['fileBase64'])
        img = Image.open(BytesIO(data))

        quality_map = {"low": 15, "medium": 35, "high": 70}
        quality = quality_map.get(msg['quality'], 50)

        out_dir = get_output_dir()
        out_path = os.path.join(out_dir, f"image - {APP_BRAND}.jpg")

        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(out_path, format="JPEG", quality=quality, optimize=True)

        if platform.system() == "Windows":
            subprocess.run(['explorer', out_dir], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        elif platform.system() == "Darwin":
            subprocess.run(['open', out_dir], capture_output=True)
        else:
            subprocess.run(['xdg-open', out_dir], capture_output=True)

        return {"success": True, "path": out_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_msg(message):
    try:
        content = json.dumps(message, ensure_ascii=False).encode('utf-8')
        sys.stdout.buffer.write(struct.pack('I', len(content)))
        sys.stdout.buffer.write(content)
        sys.stdout.buffer.flush()
    except Exception as e:
        logger.error(f"Send error: {e}")


def read_msg():
    try:
        raw_len = sys.stdin.buffer.read(4)
        if not raw_len or len(raw_len) < 4:
            return None
        length = struct.unpack('I', raw_len)[0]
        if length > 50 * 1024 * 1024:
            return None
        return json.loads(sys.stdin.buffer.read(length).decode('utf-8'))
    except Exception as e:
        logger.error(f"Read error: {e}")
        return None


def main():
    logger.info("Tmura Native Host v3.0")
    setup_pil()

    while True:
        try:
            msg = read_msg()
            if not msg:
                break

            action = msg.get('action')
            media_type = msg.get('mediaType', 'image')

            if action == 'compress':
                if media_type == 'video':
                    send_msg(convert_video(msg))
                else:
                    send_msg(compress_image(msg))
            elif action == 'save':
                if media_type == 'video':
                    send_msg(convert_video(msg))
                else:
                    send_msg(save_image_to_folder(msg))
            elif action == 'ping':
                send_msg({"success": True, "message": "Pong", "version": "3.0"})
            elif action == 'status':
                send_msg({"success": True, "status": "running", "version": "3.0"})
            else:
                send_msg({"success": False, "error": f"Unknown action: {action}"})
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            send_msg({"success": False, "error": str(e)})
            break

    logger.info("Native Host stopped")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        logger.critical(f"Unhandled: {e}")
        sys.exit(1)
