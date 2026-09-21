import logging
import os
import tempfile
import uuid
from dataclasses import dataclass
from typing import Optional

import yt_dlp

logger = logging.getLogger(__name__)


class _YdlLogger:
    def debug(self, msg):
        if not msg.startswith("[debug] "):
            logger.info("yt-dlp: %s", msg)

    def info(self, msg):
        logger.info("yt-dlp: %s", msg)

    def warning(self, msg):
        logger.warning("yt-dlp: %s", msg)

    def error(self, msg):
        logger.error("yt-dlp: %s", msg)


class DownloadError(Exception):
    """Raised when yt-dlp fails to fetch the requested media."""


@dataclass
class DownloadResult:
    file_path: str
    caption: Optional[str]
    author: Optional[str]


def _load_cookies_path() -> str:
    """Path to a cookiejar yt-dlp reads from and writes back to, so a
    session started via username/password login is reused across
    requests instead of logging in again every time."""
    path = os.path.join(tempfile.gettempdir(), "instagram_cookies.txt")
    content = os.environ.get("INSTAGRAM_COOKIES")
    if content and not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return path


_COOKIES_PATH = _load_cookies_path()
_IG_USERNAME = os.environ.get("INSTAGRAM_USERNAME")
_IG_PASSWORD = os.environ.get("INSTAGRAM_PASSWORD")

if _IG_USERNAME and _IG_PASSWORD:
    logger.info("Login do Instagram configurado para o usuário: %s", _IG_USERNAME)
else:
    logger.warning("INSTAGRAM_USERNAME/INSTAGRAM_PASSWORD não configurados — downloads serão anônimos.")


def download_video(url: str, download_dir: str) -> DownloadResult:
    os.makedirs(download_dir, exist_ok=True)
    output_template = os.path.join(download_dir, f"{uuid.uuid4().hex}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": False,
        "logger": _YdlLogger(),
        "noplaylist": True,
        "retries": 3,
        "cookiefile": _COOKIES_PATH,
    }
    if _IG_USERNAME and _IG_PASSWORD:
        ydl_opts["username"] = _IG_USERNAME
        ydl_opts["password"] = _IG_PASSWORD

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(str(exc)) from exc

    if not os.path.exists(file_path):
        base, _ = os.path.splitext(file_path)
        candidate = f"{base}.mp4"
        if os.path.exists(candidate):
            file_path = candidate
        else:
            raise DownloadError("Não foi possível localizar o arquivo baixado.")

    author = info.get("uploader") or info.get("uploader_id") or info.get("channel")
    caption = info.get("description") or info.get("title")

    return DownloadResult(file_path=file_path, caption=caption, author=author)
