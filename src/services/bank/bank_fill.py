"""Заполнение банковского PDF данными компании и суммой перевода."""

import logging
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from src.infrastructure.document.pdf_get_page_size import PdfGetPageSize
from src.infrastructure.document.sign_pdf import PdfSigner
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.services.bank.bank_models import BANK_FIELD_ORDER, PDF_FIELDS
from src.services.signing.context import SignaturePositions
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def fill_bank_pdf(
    input_pdf: Path,
    output_pdf: Path,
    amount: float,
    date: str,
    company_profile: CompanyProfile,
    bank_details: BankDetails,
    signature: Path | None = None,
) -> None:
    """
    Накладывает на шаблон банка реквизиты, сумму и подпись
    и сохраняет новый PDF.
    """

    input_pdf = resolve_project_path(input_pdf)
    output_pdf = resolve_project_path(output_pdf)
    signature = resolve_project_path(signature) if signature is not None else None
    if signature is None:
        msg = "Signature not found."
        raise FileNotFoundError(msg)

    LOGGER.info("Filling bank PDF: input=%s output=%s", input_pdf, output_pdf)
    reader = PdfReader(str(input_pdf))
    page = reader.pages[0]

    packet = BytesIO()
    overlay = canvas.Canvas(packet, pagesize=PdfGetPageSize.get_page_size(page))
    draw_form_fields(overlay, build_bank_form_data(amount, date, company_profile, bank_details))
    signature_bytes = SignatureCipher.decrypt_bytes(signature)
    PdfSigner.draw_signature(
        pdf_canvas=overlay,
        signature=signature_bytes,
        position=SignaturePositions.BANK,
    )
    overlay.save()
    packet.seek(0)

    overlay_page = PdfReader(packet).pages[0]
    page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(page)
    for other_page in reader.pages[1:]:
        writer.add_page(other_page)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as file_handle:
        writer.write(file_handle)

    LOGGER.info("Generated filled bank PDF: %s", output_pdf)


def build_bank_form_data(
    amount: float,
    date: str,
    company_profile: CompanyProfile,
    bank_details: BankDetails,
) -> dict[str, str]:
    """Собирает значения полей для наложения на PDF банка."""

    payment_number = company_profile.payment_number or ""
    payment_code = company_profile.payment_code or ""
    payment_description = company_profile.payment_description or ""
    recipient = bank_details.account_holder
    registration_number = company_profile.registration_number or ""
    account_number = bank_details.account_number
    city = company_profile.city or ""

    return {
        "number": payment_number,
        "code": payment_code,
        "year": date[-4:],
        "description": payment_description,
        "recipient": recipient,
        "registration_number": registration_number,
        "account_number": account_number,
        "amount": f"{amount:.2f} €",
        "place_and_date": f"{city} {date}",
    }


def draw_form_fields(pdf_canvas: canvas.Canvas, values: dict[str, str]) -> None:
    pdf_canvas.setFont("Helvetica", 9)
    for field_name in BANK_FIELD_ORDER:
        value = values.get(field_name)
        if value is not None:
            field = PDF_FIELDS[field_name]
            pdf_canvas.drawString(field["x"], field["y"], str(value))


def resolve_project_path(path: Path) -> Path:
    """Резолвит относительный путь от корня проекта."""

    if path.is_absolute():
        return path

    return EnvVar.PROJECT_ROOT / path
