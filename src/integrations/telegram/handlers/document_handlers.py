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

    def invoice(self) -> None:
        self.telegram.send_message(BotInfo.GENERATING_INVOICE)
        try:
            generate_and_send_invoice()
        except ValueError as error:
            self.telegram.send_message(str(error))
            return
        self.telegram.send_message(BotInfo.INVOICE_SENT)

    def bank(self) -> None:
        print("BANK HANDLER CALLED")

        self.telegram.send_message(BotInfo.FILL_BANK_PDF)

        try:
            print("BEFORE FILL")
            bank_pdf_path = fill_bank_pdf_with_data()
            print("AFTER FILL")
            self.telegram.send_document(bank_pdf_path)
        except Exception as error:
            print("BANK EXCEPTION:", repr(error))
            raise

    def transfer_request(self) -> None:
        try:
            transfer_request_pdf_path = generate_transfer_request_pdf(
                amount=EnvVar.get_required_env("INVOICE_AMOUNT"),
            )
        except ValueError as error:
            self.telegram.send_message(str(error))
            return
        self.telegram.send_document(transfer_request_pdf_path)
        self.telegram.send_message(Message.TRANSACTION_REQUEST_GENERATED)
