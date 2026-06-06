from src.logging_config import configure_logging
from src.utils.credentials import EnvVar
from src.workflows.bricks.fetch_bank_email import fetch_bank_email_workflow


def main() -> int:
    configure_logging()
    EnvVar.get_dotenv()

    fetch_bank_email_workflow()

    # telegram_client.send_document(document_path=pdf_path)
    # docx_path = pdf_path.with_suffix(".docx")
    # telegram_client.send_document(document_path=docx_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
