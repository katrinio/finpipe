from email import message_from_bytes

from src.services.email.email_builder import EmailBuilder, build_email


def _get_attachment_filenames(raw_message: bytes) -> list[str]:
    message = message_from_bytes(raw_message)
    return [part.get_filename() for part in message.walk() if part.get_content_disposition() == "attachment"]


def test_build_email_without_attachments() -> None:
    raw_message = build_email(
        to_email="recipient@example.com",
        subject="Invoice",
        body="Plain text body",
    )

    message = message_from_bytes(raw_message)
    assert message["To"] == "recipient@example.com"
    assert message["Subject"] == "Invoice"
    assert message.get_payload()[0].get_payload(decode=True).decode("utf-8").strip() == "Plain text body"
    assert _get_attachment_filenames(raw_message) == []


def test_build_email_with_single_attachment(tmp_path) -> None:
    attachment = tmp_path / "invoice.pdf"
    attachment.write_bytes(b"pdf-bytes")

    raw_message = build_email(
        to_email="recipient@example.com",
        subject="Invoice",
        body="Body",
        attachments=[attachment],
    )

    assert _get_attachment_filenames(raw_message) == ["invoice.pdf"]


def test_email_builder_class_uses_same_api(tmp_path) -> None:
    attachment = tmp_path / "invoice.pdf"
    attachment.write_bytes(b"pdf-bytes")

    raw_message = EmailBuilder().build_email(
        to_email="recipient@example.com",
        subject="Invoice",
        body="Body",
        attachments=[attachment],
    )

    assert _get_attachment_filenames(raw_message) == ["invoice.pdf"]


def test_build_email_with_multiple_attachments(tmp_path) -> None:
    first = tmp_path / "invoice.pdf"
    second = tmp_path / "details.txt"
    first.write_bytes(b"pdf-bytes")
    second.write_bytes(b"text-bytes")

    raw_message = build_email(
        to_email="recipient@example.com",
        subject="Invoice",
        body="Body",
        attachments=[first, second],
    )

    assert _get_attachment_filenames(raw_message) == ["invoice.pdf", "details.txt"]
