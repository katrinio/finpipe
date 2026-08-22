from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
from unittest.mock import patch

import pytest

from src.workflows import run_conversion_request_delivery
from src.workflows.run_conversion_request_delivery import generate_and_send_conversion_request


def test_parallel_conversion_request_deliveries_use_isolated_temporary_paths() -> None:
    barrier = Barrier(2)
    lock = Lock()
    output_paths: list[Path] = []
    delivered: list[tuple[int, bytes]] = []

    def fake_generate_conversion_order_pdf(
        telegram_id: int,
        conversion_amount_eur: float,
        bank_received_amount_eur: float,
        output_dir: Path,
    ) -> Path:
        output_path = output_dir / "conversion-request.pdf"
        output_path.write_bytes(f"{telegram_id}:{conversion_amount_eur}".encode())
        output_path.with_suffix(".docx").write_bytes(b"docx")
        with lock:
            output_paths.append(output_path)
        barrier.wait()
        return output_path

    class RecordingTelegramClient:
        def send_document(self, chat_id: int, document_path: Path) -> None:
            with lock:
                delivered.append((chat_id, document_path.read_bytes()))

    telegram = RecordingTelegramClient()
    with (
        patch.object(run_conversion_request_delivery, "generate_conversion_order_pdf", side_effect=fake_generate_conversion_order_pdf),
        ThreadPoolExecutor(max_workers=2) as executor,
    ):
        futures = [
            executor.submit(generate_and_send_conversion_request, telegram, chat_id, amount) for chat_id, amount in ((123, 1200.5), (456, 800.0))
        ]
        for future in futures:
            future.result()

    assert len({path.parent for path in output_paths}) == 2
    assert sorted(delivered) == [(123, b"123:1200.5"), (456, b"456:800.0")]
    assert all(not path.exists() and not path.with_suffix(".docx").exists() for path in output_paths)


def test_conversion_request_delivery_cleans_files_when_send_fails() -> None:
    captured_path: Path | None = None

    def fake_generate_conversion_order_pdf(
        telegram_id: int,
        conversion_amount_eur: float,
        bank_received_amount_eur: float,
        output_dir: Path,
    ) -> Path:
        nonlocal captured_path
        captured_path = output_dir / "conversion-request.pdf"
        captured_path.write_bytes(b"result")
        captured_path.with_suffix(".docx").write_bytes(b"docx")
        return captured_path

    class FailingTelegramClient:
        def send_document(self, chat_id: int, document_path: Path) -> None:
            raise RuntimeError("Telegram unavailable")

    with (
        patch.object(run_conversion_request_delivery, "generate_conversion_order_pdf", side_effect=fake_generate_conversion_order_pdf),
        pytest.raises(RuntimeError, match="Telegram unavailable"),
    ):
        generate_and_send_conversion_request(FailingTelegramClient(), 123, 1200.5)

    assert captured_path is not None
    assert not captured_path.exists()
    assert not captured_path.with_suffix(".docx").exists()
