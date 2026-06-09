import importlib.util
import sys
import types
from pathlib import Path
from typing import Self

import pytest


def _load_sign_pdf_module(monkeypatch: pytest.MonkeyPatch):
    pil_module = types.ModuleType("PIL")

    class ImageStubModule:
        @staticmethod
        def open(path: object) -> object:
            message = "test should monkeypatch PIL.Image.open"
            raise RuntimeError(message)

    pil_module.Image = ImageStubModule
    monkeypatch.setitem(sys.modules, "PIL", pil_module)
    monkeypatch.setitem(sys.modules, "PIL.Image", ImageStubModule)

    pypdf_module = types.ModuleType("pypdf")

    class PdfReaderStub:
        def __init__(self, path: str) -> None:
            self.pages = [object()]

    pypdf_module.PdfReader = PdfReaderStub
    monkeypatch.setitem(sys.modules, "pypdf", pypdf_module)

    reportlab_module = types.ModuleType("reportlab")
    reportlab_pdfgen_module = types.ModuleType("reportlab.pdfgen")
    reportlab_canvas_module = types.ModuleType("reportlab.pdfgen.canvas")

    class CanvasStub:
        def __init__(self, packet: object, pagesize: object) -> None:
            self.packet = packet
            self.pagesize = pagesize

        def save(self) -> None:
            return None

        def drawImage(self, *args: object, **kwargs: object) -> None:
            return None

    reportlab_canvas_module.Canvas = CanvasStub
    reportlab_pdfgen_module.canvas = reportlab_canvas_module
    reportlab_module.pdfgen = reportlab_pdfgen_module
    monkeypatch.setitem(sys.modules, "reportlab", reportlab_module)
    monkeypatch.setitem(sys.modules, "reportlab.pdfgen", reportlab_pdfgen_module)
    monkeypatch.setitem(sys.modules, "reportlab.pdfgen.canvas", reportlab_canvas_module)

    document_package = types.ModuleType("src.infrastructure.document")

    class PdfGetPageSizeStub:
        @staticmethod
        def get_page_size(page: object) -> tuple[int, int]:
            return (595, 842)

    document_package.PdfGetPageSize = PdfGetPageSizeStub
    monkeypatch.setitem(sys.modules, "src.infrastructure.document", document_package)

    signing_context_module = types.ModuleType("src.services.signing.context")

    class PdfSignaturePosition:
        def __init__(self, x: int, y: int, height: int) -> None:
            self.x = x
            self.y = y
            self.height = height

    signing_context_module.PdfSignaturePosition = PdfSignaturePosition
    monkeypatch.setitem(sys.modules, "src.services.signing.context", signing_context_module)

    credentials_module = types.ModuleType("src.utils.credentials")

    class LoggerStub:
        def __init__(self) -> None:
            self.messages: list[tuple[str, object]] = []

        def warning(self, message: str, *args: object) -> None:
            self.messages.append((message, args))

    credentials_module.LOGGER = LoggerStub()
    monkeypatch.setitem(sys.modules, "src.utils.credentials", credentials_module)

    module_path = Path(__file__).resolve().parents[3] / "src" / "infrastructure" / "document" / "sign_pdf.py"
    spec = importlib.util.spec_from_file_location("tests.sign_pdf_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_get_signature_size_scales_width_to_target_height(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_sign_pdf_module(monkeypatch)
    signature_path = tmp_path / "signature.png"
    signature_path.write_bytes(b"fake image")

    class ImageStub:
        size = (200, 100)

        def __enter__(self) -> Self:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    monkeypatch.setattr(module.Image, "open", lambda path: ImageStub())

    assert module.PdfSigner._get_signature_size(signature_path, target_height=50) == (100, 50)


def test_draw_signature_logs_and_skips_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_sign_pdf_module(monkeypatch)
    signature_path = tmp_path / "missing.png"

    class CanvasStub:
        def drawImage(self, *args: object, **kwargs: object) -> None:
            message = "drawImage must not be called for a missing signature"
            raise AssertionError(message)

    module.PdfSigner.draw_signature(
        pdf_canvas=CanvasStub(),
        signature=signature_path,
        position=module.PdfSignaturePosition(x=10, y=20, height=30),
    )

    assert module.LOGGER.messages == [("Signature image does not exist: %s", (signature_path,))]


def test_draw_signature_uses_position_and_calculated_size(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_sign_pdf_module(monkeypatch)
    signature_path = tmp_path / "signature.png"
    signature_path.write_bytes(b"fake image")

    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    class CanvasStub:
        def drawImage(self, *args: object, **kwargs: object) -> None:
            calls.append((args, kwargs))

    class ImageStub:
        size = (300, 120)

        def __enter__(self) -> Self:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    monkeypatch.setattr(module.Image, "open", lambda path: ImageStub())

    module.PdfSigner.draw_signature(
        pdf_canvas=CanvasStub(),
        signature=signature_path,
        position=module.PdfSignaturePosition(x=15, y=25, height=60),
    )

    assert calls == [
        (
            (str(signature_path), 15, 25),
            {
                "width": 150,
                "height": 60,
                "mask": "auto",
            },
        )
    ]
