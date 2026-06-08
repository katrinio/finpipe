"""Координаты полей для наложения данных на банковский PDF."""

PDF_FIELDS = {
    "number": {"x": 95, "y": 388},
    "code": {"x": 115, "y": 388},
    "year": {"x": 200, "y": 388},
    "description": {"x": 237, "y": 388},
    "recipient": {"x": 210, "y": 255},
    "registration_number": {"x": 210, "y": 243},
    "account_number": {"x": 210, "y": 230},
    "amount": {"x": 440, "y": 230},
    "place_and_date": {"x": 100, "y": 125},
}

BANK_FIELD_ORDER = (
    "number",
    "code",
    "year",
    "description",
    "recipient",
    "registration_number",
    "account_number",
    "amount",
    "place_and_date",
)
