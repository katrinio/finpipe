from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.messages import BotInfo
from src.services.profile_template.exceptions import InvalidProfileTemplateError, InvalidProfileTemplateFormatError, ProfileTemplateTooLargeError
from src.services.profile_template.profile_template_service import ProfileTemplateService
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile


class ProfileHandlers:
    def __init__(self, telegram: TelegramClient, state_service: UserStateService) -> None:
        self.telegram = telegram
        self.state_service = state_service

    def handle_profile_template_upload(self, telegram_id: int, file_name: str, file_size: int, file_bytes: bytes) -> None:
        try:
            ProfileTemplateService.upload(
                telegram_id=telegram_id,
                file_name=file_name,
                file_size=file_size,
                file_bytes=file_bytes,
            )
        except InvalidProfileTemplateFormatError:
            self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_NOT_YAML)
            return
        except ProfileTemplateTooLargeError:
            self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_TOO_LARGE)
            return
        except InvalidProfileTemplateError as error:
            self.telegram.send_message(telegram_id, str(error))
            return

        self.state_service.clear_state(telegram_id)
        company_profile = CompanyProfile.get_by_owner(telegram_id)
        bank_details = BankDetails.get_by_owner(telegram_id)
        if company_profile is None or bank_details is None:
            self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_UPDATED)
            return

        self.telegram.send_message(
            telegram_id,
            (f"✅ Профиль успешно загружен.\nКомпания: {company_profile.company_name}\nБанк: {bank_details.bank_name}"),
        )

    def upload_template(self, telegram_id: int) -> None:
        self.state_service.set_state(telegram_id, UserState.WAITING_PROFILE_TEMPLATE_UPLOAD)
        self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_REQUIREMENTS)

    def download_template(self, telegram_id: int) -> None:
        self.telegram.send_document(telegram_id, document_path=Dir.PROFILE_TEMPLATE)
        self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_SENT)
