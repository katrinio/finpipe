"""Unit-тесты доставки сгенерированного инвойса в Telegram."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
from unittest.mock import patch

import pytest

from src.workflows import run_invoice_delivery
from src.workflows.run_invoice_delivery import generate_and_send_invoice
from tests.fakes.fake_telegram import FakeTelegramClient


def test_generate_and_send_invoice_sends_document_and_removes_temporary_files(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invoice-2026-06.pdf"
    docx_path = tmp_path / "invoice-2026-06.docx"
    pdf_path.write_bytes(b"pdf")
    docx_path.write_bytes(b"docx")
    telegram_client = FakeTelegramClient()

    with (
        patch.object(run_invoice_delivery, "generate_invoice_pdf", return_value=pdf_path),
        patch.object(run_invoice_delivery, "TelegramClient", return_value=telegram_client),
    ):
        generate_and_send_invoice(chat_id=123)

    assert telegram_client.sent_documents == [(123, str(pdf_path))]
    assert not pdf_path.exists()
    assert not docx_path.exists()


def test_generate_and_send_invoice_cleans_up_when_telegram_send_fails(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invoice-2026-06.pdf"
    docx_path = tmp_path / "invoice-2026-06.docx"
    pdf_path.write_bytes(b"pdf")
    docx_path.write_bytes(b"docx")
    telegram_client = FakeTelegramClient()

    with (
        patch.object(run_invoice_delivery, "generate_invoice_pdf", return_value=pdf_path),
        patch.object(run_invoice_delivery, "TelegramClient", return_value=telegram_client),
        patch.object(telegram_client, "send_document", side_effect=RuntimeError("Telegram unavailable")),
        pytest.raises(RuntimeError, match="Telegram unavailable"),
    ):
        generate_and_send_invoice(chat_id=123)

    assert not pdf_path.exists()
    assert not docx_path.exists()


def test_parallel_invoice_deliveries_use_isolated_temporary_paths() -> None:
    barrier = Barrier(2)
    lock = Lock()
    generated_paths: list[Path] = []
    delivered: list[tuple[int, bytes]] = []

    def fake_generate_invoice_pdf(telegram_id: int, output_dir: Path) -> Path:
        pdf_path = output_dir / "invoice-2026-06.pdf"
        pdf_path.write_bytes(str(telegram_id).encode())
        pdf_path.with_suffix(".docx").write_bytes(b"docx")
        with lock:
            generated_paths.append(pdf_path)
        barrier.wait()
        return pdf_path

    class RecordingTelegramClient:
        def send_document(self, chat_id: int, document_path: Path) -> None:
            with lock:
                delivered.append((chat_id, document_path.read_bytes()))

    with (
        patch.object(run_invoice_delivery, "generate_invoice_pdf", side_effect=fake_generate_invoice_pdf),
        patch.object(run_invoice_delivery, "TelegramClient", return_value=RecordingTelegramClient()),
        ThreadPoolExecutor(max_workers=2) as executor,
    ):
        futures = [executor.submit(generate_and_send_invoice, chat_id) for chat_id in (123, 456)]
        for future in futures:
            future.result()

    assert len({path.parent for path in generated_paths}) == 2
    assert sorted(delivered) == [(123, b"123"), (456, b"456")]
    assert all(not path.exists() and not path.with_suffix(".docx").exists() for path in generated_paths)
