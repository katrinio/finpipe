"""Сборка MIME-писем для отправки через интеграции почты."""

from __future__ import annotations

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


class EmailBuilder:
    """Строит MIME-письмо без привязки к конкретному провайдеру."""

    def build_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: list[Path] | None = None,
    ) -> bytes:
        """Собирает MIME-письмо с plain text и вложениями."""

        message = MIMEMultipart()
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))

        for attachment_path in attachments or []:
            message.attach(self._build_attachment(attachment_path))

        return message.as_bytes()

    def _build_attachment(self, attachment_path: Path) -> MIMEBase:
        """Создаёт MIME-часть для вложения."""

        with attachment_path.open("rb") as attachment_file:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment_file.read())

        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=attachment_path.name)
        return part


def build_email(
    to_email: str,
    subject: str,
    body: str,
    attachments: list[Path] | None = None,
) -> bytes:
    """Собирает MIME-письмо через стандартный builder."""

    return EmailBuilder().build_email(to_email=to_email, subject=subject, body=body, attachments=attachments)
