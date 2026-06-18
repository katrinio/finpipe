"""Тесты флоу «Банковский день»: email → подтверждение + конвертация → 3 документа."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.ui.buttons import DocumentsMenuButtons
from src.integrations.telegram.ui.messages import BankMessages
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser
from tests.fakes.fake_telegram import FakeTelegramClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ready_profile(monkeypatch) -> None:
    """Подставляет заглушки, имитирующие полный профиль с подписью."""
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.SystemStatusService.get_status",
        lambda _telegram_id: SimpleNamespace(company=True, bank_details=True),
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.Signature.is_usable", lambda _telegram_id: True)


# ---------------------------------------------------------------------------
# Button routing
# ---------------------------------------------------------------------------


def test_bank_day_button_is_routed(tmp_path: Path) -> None:
    """Кнопка «Банковский день» регистрируется в роутере и вызывает обработчик."""
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    # Прерываем на первой же проверке готовности — значит роутер дошёл до handler.bank_day().
    bot.process_update(
        {
            "update_id": 99,
            "message": {
                "text": DocumentsMenuButtons.BANK_DAY,
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    # Должен прийти хотя бы один ответ (ошибка профиля или прогресс)
    assert len(telegram_client.sent_messages) >= 1


# ---------------------------------------------------------------------------
# Проверки готовности
# ---------------------------------------------------------------------------


def test_bank_day_requires_complete_profile(tmp_path: Path, monkeypatch) -> None:
    """Без профиля или реквизитов — сообщение об ошибке без дальнейшей работы."""
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.SystemStatusService.get_status",
        lambda _telegram_id: SimpleNamespace(company=False, bank_details=True),
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.Signature.is_usable", lambda _telegram_id: True)

    bot.handlers.document_handler.bank_day(123)

    assert telegram_client.sent_messages == [BankMessages.Validation.PROFILE_REQUIRED]


def test_bank_day_requires_signature(tmp_path: Path, monkeypatch) -> None:
    """Без подписи — сообщение об ошибке."""
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.SystemStatusService.get_status",
        lambda _telegram_id: SimpleNamespace(company=True, bank_details=True),
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.Signature.is_usable", lambda _telegram_id: False)

    bot.handlers.document_handler.bank_day(123)

    assert telegram_client.sent_messages == [BankMessages.Validation.SIGNATURE_REQUIRED]


# ---------------------------------------------------------------------------
# Gmail ошибки
# ---------------------------------------------------------------------------


def test_bank_day_reports_gmail_not_configured(tmp_path: Path, monkeypatch) -> None:
    """Если Gmail не настроен — сообщение BANK_EMAIL_NOT_CONFIGURED."""
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    _ready_profile(monkeypatch)
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.fetch_bank_email_workflow",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("Gmail not configured")),
    )

    bot.handlers.document_handler.bank_day(123)

    assert BankMessages.Validation.BANK_EMAIL_NOT_CONFIGURED in telegram_client.sent_messages


def test_bank_day_reports_no_new_email(tmp_path: Path, monkeypatch) -> None:
    """Если нового письма нет — сообщение NOT_FOUND."""
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    _ready_profile(monkeypatch)
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.fetch_bank_email_workflow",
        lambda **_kwargs: None,
    )

    bot.handlers.document_handler.bank_day(123)

    assert BankMessages.Search.NOT_FOUND in telegram_client.sent_messages


# ---------------------------------------------------------------------------
# Основной флоу
# ---------------------------------------------------------------------------


def test_bank_day_sends_three_documents(tmp_path: Path, monkeypatch) -> None:
    """Успешный флоу отправляет ровно 3 документа: оригинал, подтверждение, конвертация."""
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    original_pdf = tmp_path / "original.pdf"
    original_pdf.write_bytes(b"%PDF-1.7\noriginal")
    filled_pdf = tmp_path / "filled.pdf"
    filled_pdf.write_bytes(b"%PDF-1.7\nfilled")
    conversion_pdf = tmp_path / "conversion.pdf"
    conversion_pdf.write_bytes(b"%PDF-1.7\nconversion")

    _ready_profile(monkeypatch)
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.fetch_bank_email_workflow",
        lambda **_kwargs: original_pdf,
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.extract_amount", lambda _pdf: 500.0)
    monkeypatch.setattr(
        bot.handlers.document_handler,
        "_fill_bank_confirmation_pdf",
        lambda _telegram_id, _input_pdf, _amount: filled_pdf,
    )
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.generate_conversion_order_pdf",
        lambda **_kwargs: conversion_pdf,
    )

    bot.handlers.document_handler.bank_day(123)

    assert len(telegram_client.sent_documents) == 3
    sent_paths = [path for _chat_id, path in telegram_client.sent_documents]
    assert str(original_pdf) in sent_paths
    assert str(filled_pdf) in sent_paths
    assert str(conversion_pdf) in sent_paths


def test_bank_day_saves_extracted_amount_to_user_config(tmp_path: Path, monkeypatch) -> None:
    """Сумма из письма банка сохраняется в UserConfig.bank_received_amount_eur."""
    from src.storage.orm import UserConfig

    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    original_pdf = tmp_path / "original.pdf"
    original_pdf.write_bytes(b"%PDF-1.7\noriginal")
    filled_pdf = tmp_path / "filled.pdf"
    filled_pdf.write_bytes(b"%PDF-1.7\nfilled")
    conversion_pdf = tmp_path / "conversion.pdf"
    conversion_pdf.write_bytes(b"%PDF-1.7\nconversion")

    _ready_profile(monkeypatch)
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.fetch_bank_email_workflow",
        lambda **_kwargs: original_pdf,
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.extract_amount", lambda _pdf: 777.5)
    monkeypatch.setattr(
        bot.handlers.document_handler,
        "_fill_bank_confirmation_pdf",
        lambda _telegram_id, _input_pdf, _amount: filled_pdf,
    )
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.generate_conversion_order_pdf",
        lambda **_kwargs: conversion_pdf,
    )

    bot.handlers.document_handler.bank_day(123)

    config = UserConfig.get_by_owner(123)
    assert config is not None
    assert config.bank_received_amount_eur == pytest.approx(777.5)


def test_bank_day_sends_done_message_on_success(tmp_path: Path, monkeypatch) -> None:
    """После успешного флоу отправляется финальное сообщение BankDay.DONE."""
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    original_pdf = tmp_path / "original.pdf"
    original_pdf.write_bytes(b"%PDF-1.7\noriginal")
    filled_pdf = tmp_path / "filled.pdf"
    filled_pdf.write_bytes(b"%PDF-1.7\nfilled")
    conversion_pdf = tmp_path / "conversion.pdf"
    conversion_pdf.write_bytes(b"%PDF-1.7\nconversion")

    _ready_profile(monkeypatch)
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.fetch_bank_email_workflow",
        lambda **_kwargs: original_pdf,
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.extract_amount", lambda _pdf: 100.0)
    monkeypatch.setattr(
        bot.handlers.document_handler,
        "_fill_bank_confirmation_pdf",
        lambda _telegram_id, _input_pdf, _amount: filled_pdf,
    )
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.generate_conversion_order_pdf",
        lambda **_kwargs: conversion_pdf,
    )

    bot.handlers.document_handler.bank_day(123)

    assert telegram_client.sent_messages[-1] == BankMessages.BankDay.DONE


def test_bank_day_cleans_up_files_on_error(tmp_path: Path, monkeypatch) -> None:
    """При ошибке в процессе все временные файлы удаляются."""
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    original_pdf = tmp_path / "original.pdf"
    original_pdf.write_bytes(b"%PDF-1.7\noriginal")
    filled_pdf = tmp_path / "filled.pdf"
    filled_pdf.write_bytes(b"%PDF-1.7\nfilled")

    _ready_profile(monkeypatch)
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.fetch_bank_email_workflow",
        lambda **_kwargs: original_pdf,
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.extract_amount", lambda _pdf: 100.0)
    monkeypatch.setattr(
        bot.handlers.document_handler,
        "_fill_bank_confirmation_pdf",
        lambda _telegram_id, _input_pdf, _amount: filled_pdf,
    )
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.generate_conversion_order_pdf",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("template missing")),
    )

    bot.handlers.document_handler.bank_day(123)

    # Оригинальный PDF и подтверждение должны быть удалены
    assert not original_pdf.exists()
    assert not filled_pdf.exists()
    # Ошибка должна быть сообщена пользователю
    assert any("template missing" in msg for msg in telegram_client.sent_messages)
