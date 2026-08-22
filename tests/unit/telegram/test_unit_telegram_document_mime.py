from pathlib import Path
from typing import Any, cast

import pytest

from src.integrations.telegram.client import TelegramClient


class RecordingHttpClient:
    def __init__(self) -> None:
        self.files: dict[str, object] | None = None

    def post(self, _url: str, **kwargs: Any) -> None:
        self.files = kwargs["files"]


@pytest.mark.parametrize(
    ("file_name", "expected_mime_type"),
    [
        ("invoice.pdf", "application/pdf"),
        ("profile_template.yaml", "application/yaml"),
    ],
)
def test_send_document_uses_mime_type_matching_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
    expected_mime_type: str,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    document_path = tmp_path / file_name
    document_path.write_bytes(b"document")
    http = RecordingHttpClient()

    TelegramClient(http_client=cast(Any, http)).send_document(123, document_path)

    assert http.files is not None
    document = http.files["document"]
    assert isinstance(document, tuple)
    assert document[2] == expected_mime_type
