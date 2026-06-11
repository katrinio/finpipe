from src.constants import Message
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.messages import BotInfo
from src.utils.credentials import EnvVar
from src.workflows.run_invoice_delivery import generate_and_send_invoice
from src.workflows.tasks.fill_bank_pdf import fill_bank_pdf_with_data
from src.workflows.tasks.generate_transfer_request import generate_transfer_request_pdf


class DocumentHandlers:
    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def invoice(self, telegram_id: int) -> None:
        self.telegram.send_message(telegram_id, BotInfo.GENERATING_INVOICE)
        try:
            generate_and_send_invoice(telegram_id)
        except ValueError as error:
            self.telegram.send_message(telegram_id, str(error))
            return
        self.telegram.send_message(telegram_id, BotInfo.INVOICE_SENT)

    def set_invoice_amount(self, telegram_id: int) -> None:
        self.telegram.send_message(telegram_id, "set_invoice_amount")

    def get_invoice_amount(self, telegram_id: int) -> None:
        self.telegram.send_message(telegram_id, "get_invoice_amount")

    def bank(self, telegram_id: int) -> None:

        self.telegram.send_message(telegram_id, BotInfo.FILL_BANK_PDF)

        try:
            bank_pdf_path = fill_bank_pdf_with_data()
            self.telegram.send_document(telegram_id, bank_pdf_path)
        except Exception as error:
            print("BANK EXCEPTION:", repr(error))
            raise

    def transfer_request(self, telegram_id: int) -> None:
        try:
            transfer_request_pdf_path = generate_transfer_request_pdf(
                amount=EnvVar.get_required_env("INVOICE_AMOUNT"),
            )
        except ValueError as error:
            self.telegram.send_message(telegram_id, str(error))
            return
        self.telegram.send_document(telegram_id, transfer_request_pdf_path)
        self.telegram.send_message(telegram_id, Message.TRANSACTION_REQUEST_GENERATED)
