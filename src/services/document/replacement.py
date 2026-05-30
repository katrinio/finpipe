from src.services.invoice.invoice_models import InvoiceTemplateDetails
from src.services.transfer_request.transfer_request_models import TransferRequestTemplateDetails


class Replacement:
    @classmethod
    def build_replacements(cls, data: dict[str, str], details: InvoiceTemplateDetails | TransferRequestTemplateDetails) -> dict[str, str]:
        replacements: dict[str, str] = {}

        for field_name, placeholder_names in details.placeholder_aliases.items():
            value = str(data[field_name])

            for placeholder_name in placeholder_names:
                placeholder = placeholder_name if placeholder_name.startswith("{{") else f"{{{{{placeholder_name}}}}}"

                replacements[placeholder] = value

        return replacements
