import os
import uuid
from dataclasses import dataclass
from typing import Optional

import yt_dlp

from .config import COOKIES_FILE


class DownloadError(Exception):
    """Raised when yt-dlp fails to fetch the requested media."""


@dataclass
class DownloadResult:
    file_path: str
    caption: Optional[str]
    author: Optional[str]


def download_video(url: str, download_dir: str) -> DownloadResult:
    os.makedirs(download_dir, exist_ok=True)
    output_template = os.path.join(download_dir, f"{uuid.uuid4().hex}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 3,
    }
    if COOKIES_FILE:
        ydl_opts["cookiefile"] = COOKIES_FILE

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
