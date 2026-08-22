"""Workflow генерации Conversion Request и доставки в Telegram."""

import logging
import tempfile
from pathlib import Path

from src.integrations.telegram.client import TelegramClient
from src.utils.files import delete_file
from src.workflows.tasks.generate_conversion_order import generate_conversion_order_pdf

LOGGER = logging.getLogger(__name__)


def generate_and_send_conversion_request(
    telegram: TelegramClient,
    chat_id: int,
    amount_eur: float,
) -> None:
    """Генерирует Conversion Request, отправляет PDF и удаляет временные файлы."""

    with tempfile.TemporaryDirectory(prefix=f"finpipe-conversion-request-{chat_id}-") as temporary_dir:
        output_dir = Path(temporary_dir)
        conversion_path: Path | None = None

        try:
            conversion_path = generate_conversion_order_pdf(
                telegram_id=chat_id,
                conversion_amount_eur=amount_eur,
                bank_received_amount_eur=amount_eur,
                output_dir=output_dir,
            )
            telegram.send_document(chat_id, document_path=conversion_path)
        finally:
            if conversion_path is not None:
                delete_file(conversion_path, LOGGER)
                delete_file(conversion_path.with_suffix(".docx"), LOGGER)
