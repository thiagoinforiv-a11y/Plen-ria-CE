import asyncio
import logging
import os
import re

from telegram import Update
from telegram.ext import ContextTypes

from .config import DOWNLOAD_DIR, MAX_FILE_SIZE_MB
from .downloader import DownloadError, download_video

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:instagram\.com|instagr\.am|facebook\.com|fb\.watch)/\S+",
    re.IGNORECASE,
)

WELCOME_TEXT = (
    "Olá! Me envie um link de vídeo público do Instagram ou Facebook que eu "
    "baixo o vídeo e te devolvo aqui com a legenda e o perfil que postou."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(WELCOME_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.text:
        return

    match = URL_PATTERN.search(message.text)
    if not match:
        await message.reply_text(
            "Não encontrei um link do Instagram ou Facebook nessa mensagem."
        )
        return

    url = match.group(0)
    status_message = await message.reply_text("Baixando o vídeo, aguarde...")

    try:
        result = await _download_async(url)
    except DownloadError as exc:
        logger.warning("Falha ao baixar %s: %s", url, exc)
        await status_message.edit_text(
            "Não consegui baixar esse vídeo. Verifique se o link é público "
            "e tente novamente."
        )
        return
    except Exception:
        logger.exception("Erro inesperado ao baixar %s", url)
        await status_message.edit_text("Ocorreu um erro inesperado ao baixar o vídeo.")
        return

    file_path = result.file_path
    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            await status_message.edit_text(
                f"O vídeo tem {size_mb:.1f}MB, acima do limite de "
                f"{MAX_FILE_SIZE_MB}MB que o bot consegue enviar pelo Telegram."
            )
            return

        author = result.author or "desconhecido"
        author_display = author if author.startswith("@") else f"@{author}"
        caption_text = (result.caption or "(sem legenda)").strip()

        full_caption = f"👤 Perfil: {author_display}\n\n📝 Legenda:\n{caption_text}"
        if len(full_caption) > 1024:
            full_caption = full_caption[:1021] + "..."

        with open(file_path, "rb") as video_file:
            await message.reply_video(video=video_file, caption=full_caption)

        await status_message.delete()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


async def _download_async(url: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_video, url, DOWNLOAD_DIR)
