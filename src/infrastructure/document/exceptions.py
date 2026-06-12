"""Исключения инфраструктуры рендеринга документов."""


class DocumentConversionError(RuntimeError):
    """Ошибка конвертации DOCX в PDF."""


class UnsupportedDocumentBackendError(DocumentConversionError):
    """Запрошен неподдерживаемый backend конвертации документа."""
