import logging
import os
import subprocess
import sys

from src.logging_config import SensitiveDataFormatter


def test_sensitive_formatter_redacts_all_configured_secrets(monkeypatch) -> None:
    secrets = {
        "DATABASE_URL": "postgresql+psycopg://finpipe:database-secret@postgres:5432/finpipe",
        "TELEGRAM_BOT_TOKEN": "123456:telegram-secret",
        "SIGNATURE_ENCRYPTION_KEY": "signature-secret",
        "BOT_OWNER_TELEGRAM_ID": "987654321",
    }
    for name, value in secrets.items():
        monkeypatch.setenv(name, value)

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg=" ".join(secrets.values()),
        args=(),
        exc_info=None,
    )
    rendered = SensitiveDataFormatter("%(message)s").format(record)

    assert all(secret not in rendered for secret in secrets.values())
    assert "database-secret" not in rendered


def test_urllib3_debug_url_cannot_log_telegram_token() -> None:
    token = "123456:telegram-secret"
    script = """
import logging
from src.logging_config import configure_logging
configure_logging(logging.DEBUG)
logging.getLogger('urllib3.connectionpool').debug('POST /bot%s/sendDocument', __import__('os').environ['TELEGRAM_BOT_TOKEN'])
"""
    process_env = os.environ.copy()
    process_env["TELEGRAM_BOT_TOKEN"] = token
    completed = subprocess.run(
        [sys.executable, "-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        env=process_env,
    )

    assert completed.returncode == 0
    assert token not in completed.stdout
