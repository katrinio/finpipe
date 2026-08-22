from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
from unittest.mock import patch

import pytest

from src.infrastructure.security.exceptions import SignatureDecryptionError
from src.storage.orm.user.user_config import UserConfig
from src.workflows import run_bank_confirmation_delivery
from src.workflows.run_bank_confirmation_delivery import generate_and_send_bank_confirmation


class SuccessfulTelegramClient:
    def send_document(self, chat_id: int, document_path: Path) -> None:
        return None


def test_parallel_bank_confirmation_deliveries_use_isolated_temporary_paths() -> None:
    barrier = Barrier(2)
    lock = Lock()
    source_paths: list[Path] = []
    output_paths: list[Path] = []
    delivered: list[tuple[int, bytes]] = []

    def fake_generate_bank_confirmation(telegram_id: int, bank_template: Path, output_dir: Path, amount: float) -> Path:
        output_path = output_dir / "bank-confirmation.pdf"
        output_path.write_bytes(str(telegram_id).encode())
        with lock:
            source_paths.append(bank_template)
            output_paths.append(output_path)
        barrier.wait()
        return output_path

    class RecordingTelegramClient:
        def send_document(self, chat_id: int, document_path: Path) -> None:
            with lock:
                delivered.append((chat_id, document_path.read_bytes()))

    telegram = RecordingTelegramClient()
    with (
        patch.object(run_bank_confirmation_delivery, "extract_amount", return_value=1200.5),
        patch.object(run_bank_confirmation_delivery, "generate_bank_confirmation", side_effect=fake_generate_bank_confirmation),
        ThreadPoolExecutor(max_workers=2) as executor,
    ):
        futures = [executor.submit(generate_and_send_bank_confirmation, telegram, chat_id, b"%PDF-source") for chat_id in (123, 456)]
        for future in futures:
            future.result()

    assert len({path.parent for path in source_paths}) == 2
    assert sorted(delivered) == [(123, b"123"), (456, b"456")]
    assert all(not path.exists() for path in source_paths + output_paths)


def test_bank_confirmation_delivery_cleans_files_when_send_fails() -> None:
    captured_paths: list[Path] = []

    def fake_generate_bank_confirmation(telegram_id: int, bank_template: Path, output_dir: Path, amount: float) -> Path:
        output_path = output_dir / "bank-confirmation.pdf"
        output_path.write_bytes(b"result")
        captured_paths.extend([bank_template, output_path])
        return output_path

    class FailingTelegramClient:
        def send_document(self, chat_id: int, document_path: Path) -> None:
            raise RuntimeError("Telegram unavailable")

    with (
        patch.object(run_bank_confirmation_delivery, "extract_amount", return_value=1200.5),
        patch.object(run_bank_confirmation_delivery, "generate_bank_confirmation", side_effect=fake_generate_bank_confirmation),
        pytest.raises(RuntimeError, match="Telegram unavailable"),
    ):
        generate_and_send_bank_confirmation(FailingTelegramClient(), 123, b"%PDF-source")

    assert all(not path.exists() for path in captured_paths)


@pytest.mark.parametrize(
    "generation_error",
    [
        RuntimeError("PDF generation failed"),
        SignatureDecryptionError("Signature is invalid"),
    ],
)
def test_bank_amount_is_unchanged_when_generation_fails(generation_error: Exception) -> None:
    UserConfig.upsert(telegram_id=123, bank_received_amount_eur=100.0)

    with (
        patch.object(run_bank_confirmation_delivery, "extract_amount", return_value=200.0),
        patch.object(run_bank_confirmation_delivery, "generate_bank_confirmation", side_effect=generation_error),
        pytest.raises(type(generation_error), match=str(generation_error)),
    ):
        generate_and_send_bank_confirmation(SuccessfulTelegramClient(), 123, b"%PDF-source")

    config = UserConfig.get_by_owner(123)
    assert config is not None
    assert config.bank_received_amount_eur == 100.0


def test_bank_amount_is_unchanged_when_profile_is_missing() -> None:
    UserConfig.upsert(telegram_id=123, bank_received_amount_eur=100.0)

    with (
        patch.object(run_bank_confirmation_delivery, "extract_amount", return_value=200.0),
        pytest.raises(ValueError, match="Банковские реквизиты не настроены"),
    ):
        generate_and_send_bank_confirmation(SuccessfulTelegramClient(), 123, b"%PDF-source")

    config = UserConfig.get_by_owner(123)
    assert config is not None
    assert config.bank_received_amount_eur == 100.0


def test_bank_amount_is_unchanged_when_telegram_delivery_fails() -> None:
    UserConfig.upsert(telegram_id=123, bank_received_amount_eur=100.0)

    def fake_generate_bank_confirmation(telegram_id: int, bank_template: Path, output_dir: Path, amount: float) -> Path:
        output_path = output_dir / "bank-confirmation.pdf"
        output_path.write_bytes(b"result")
        return output_path

    class FailingTelegramClient:
        def send_document(self, chat_id: int, document_path: Path) -> None:
            raise RuntimeError("Telegram unavailable")

    with (
        patch.object(run_bank_confirmation_delivery, "extract_amount", return_value=200.0),
        patch.object(run_bank_confirmation_delivery, "generate_bank_confirmation", side_effect=fake_generate_bank_confirmation),
        pytest.raises(RuntimeError, match="Telegram unavailable"),
    ):
        generate_and_send_bank_confirmation(FailingTelegramClient(), 123, b"%PDF-source")

    config = UserConfig.get_by_owner(123)
    assert config is not None
    assert config.bank_received_amount_eur == 100.0


def test_bank_amount_is_updated_after_generation_and_delivery_succeed() -> None:
    UserConfig.upsert(telegram_id=123, bank_received_amount_eur=100.0)

    def fake_generate_bank_confirmation(telegram_id: int, bank_template: Path, output_dir: Path, amount: float) -> Path:
        output_path = output_dir / "bank-confirmation.pdf"
        output_path.write_bytes(b"result")
        return output_path

    with (
        patch.object(run_bank_confirmation_delivery, "extract_amount", return_value=200.0),
        patch.object(run_bank_confirmation_delivery, "generate_bank_confirmation", side_effect=fake_generate_bank_confirmation),
    ):
        generate_and_send_bank_confirmation(SuccessfulTelegramClient(), 123, b"%PDF-source")

    config = UserConfig.get_by_owner(123)
    assert config is not None
    assert config.bank_received_amount_eur == 200.0
