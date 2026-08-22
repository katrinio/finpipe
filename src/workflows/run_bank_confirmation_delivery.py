"""Workflow генерации Bank Transfer Confirmation и доставки в Telegram."""

import logging
import tempfile
from pathlib import Path

from src.integrations.telegram.client import TelegramClient
from src.services.bank.bank_extract import extract_amount
from src.storage.orm.user.user_config import UserConfig
from src.utils.files import delete_file
from src.workflows.tasks.generate_bank_confirmation import generate_bank_confirmation

LOGGER = logging.getLogger(__name__)


def generate_and_send_bank_confirmation(
    telegram: TelegramClient,
    chat_id: int,
    source_pdf: bytes,
) -> None:
    """Генерирует подтверждение из загруженного PDF, отправляет его и удаляет временные файлы."""

    with tempfile.TemporaryDirectory(prefix=f"finpipe-bank-confirmation-{chat_id}-") as temporary_dir:
        output_dir = Path(temporary_dir)
        source_path = output_dir / "bank-source.pdf"
        source_path.write_bytes(source_pdf)
        confirmation_path: Path | None = None

        try:
            amount = extract_amount(source_path)
            confirmation_path = generate_bank_confirmation(
                telegram_id=chat_id,
                bank_template=source_path,
                output_dir=output_dir,
                amount=amount,
            )
            telegram.send_document(chat_id, document_path=confirmation_path)
            UserConfig.upsert(telegram_id=chat_id, bank_received_amount_eur=amount)
        finally:
            delete_file(source_path, LOGGER)
            if confirmation_path is not None:
                delete_file(confirmation_path, LOGGER)
                delete_file(confirmation_path.with_suffix(".docx"), LOGGER)
