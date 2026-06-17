from typing import cast

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.handlers.command_router import CommandRouter
from src.integrations.telegram.handlers.monitoring_handler import MonitoringHandler
from src.integrations.telegram.ui.buttons import NavigationButtons, OwnerButtons
from src.integrations.telegram.ui.menu.admin_menu import build_admin_menu
from src.integrations.telegram.ui.menu.system_menu import build_system_menu
from src.storage.dependencies import StorageDependencies
from src.storage.orm import AllowedUser, UserRole
from src.storage.orm.database import Database
from src.storage.orm.system.audit_log import AuditLog
from tests.fakes.fake_storage import FakeStorage, FakeTelegramUpdateStorage
from tests.fakes.fake_telegram import FakeTelegramClient
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_monitoring_chat_status_is_handled_in_monitoring_handler(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    handler = MonitoringHandler(cast(TelegramClient, telegram))

    handled = handler.handle_message("/status", chat_id=-100123, telegram_id=777, username="owner")

    assert handled is True
    assert telegram.sent_message_payloads[-1][0] == -100123
    assert telegram.sent_message_payloads[-1][1].startswith("📊 Finpipe status")


def test_monitoring_chat_command_does_not_go_to_user_router(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    bot = TelegramBot(cast(StorageDependencies, FakeStorage({777})), telegram=cast(TelegramClient, telegram))
    bot.update_storage = FakeTelegramUpdateStorage()

    bot.process_update(
        {
            "update_id": 40,
            "message": {
                "text": "/status",
                "chat": {"id": -100123, "type": "group"},
                "from": {"id": 777, "username": "owner"},
            },
        }
    )

    assert telegram.sent_messages_with_chat_ids[-1][0] == -100123
    assert telegram.sent_messages_with_chat_ids[-1][1].startswith("📊 Finpipe status")
    assert bot.update_storage.processed == [40]


def test_unknown_monitoring_text_is_ignored(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    handler = MonitoringHandler(cast(TelegramClient, telegram))

    handled = handler.handle_message("hello", chat_id=-100123, telegram_id=777, username="owner")

    assert handled is True
    assert telegram.sent_messages == []


def test_user_router_does_not_expose_monitoring_commands(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    router = CommandRouter(telegram=cast(TelegramClient, telegram), audit_log=AuditLog)

    assert router.handle_message("/status", telegram_id=777, username="owner") is True
    assert telegram.sent_messages[-1] == "🫥 Неизвестная команда."


def test_menu_builders_do_not_show_monitoring_controls() -> None:
    assert build_system_menu(is_owner=True) == {
        "keyboard": [
            [{"text": "ℹ️ О проекте"}, {"text": "🚀 Начало работы"}],
            [{"text": "👤 Кто я"}],
            [{"text": "🏠 Домой"}],
            [{"text": "🛠️ Админка"}],
        ],
        "resize_keyboard": True,
    }
    assert build_admin_menu() == {
        "keyboard": [
            [{"text": OwnerButtons.USERS}],
            [{"text": OwnerButtons.STATISTICS}],
            [{"text": NavigationButtons.HOME}],
        ],
        "resize_keyboard": True,
    }
