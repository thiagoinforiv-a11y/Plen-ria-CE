import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .config import TELEGRAM_BOT_TOKEN
from .handlers import handle_message, help_command, start

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "Defina a variável de ambiente TELEGRAM_BOT_TOKEN antes de iniciar o bot."
        )

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
