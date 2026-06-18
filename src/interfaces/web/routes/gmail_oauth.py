"""HTTP callback entrypoint for Gmail OAuth."""

import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.integrations.gmail.exceptions import GmailOAuthError
from src.integrations.gmail.oauth_callback import GmailOAuthCallbackService
from src.integrations.gmail.settings import GmailOAuthSettings
from src.storage.orm.system.audit_log import AuditLog, AuditStatus

LOGGER = logging.getLogger(__name__)
router = APIRouter()
_AUDIT_COMMAND = "gmail_oauth_callback"


@router.get("/oauth/gmail/callback", response_class=HTMLResponse)
def gmail_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
    """Delegates Gmail OAuth callback handling to the existing application service."""

    LOGGER.info("OAuth callback received")

    if not GmailOAuthSettings.is_callback_enabled():
        return _error_response("Gmail OAuth callback is temporarily unavailable.")

    try:
        result = GmailOAuthCallbackService.handle_callback(code=code, state=state, error=error)
    except GmailOAuthError as exc:
        LOGGER.error("Callback processing failed: %s", exc)
        _audit(telegram_id=None, status=AuditStatus.FAILED, details=str(exc))
        return _error_response(str(exc))
    except Exception as exc:
        LOGGER.exception("Callback processing failed")
        _audit(telegram_id=None, status=AuditStatus.FAILED, details=f"Internal error: {type(exc).__name__}")
        return _error_response("Internal callback error.")

    if result.ok:
        _audit(telegram_id=result.telegram_id, status=AuditStatus.SUCCESS)
        return HTMLResponse("Gmail successfully connected.<br>You may close this browser window.")

    _audit(telegram_id=result.telegram_id, status=AuditStatus.FAILED, details=result.message)
    return _error_response(result.message)


def _audit(telegram_id: int | None, status: AuditStatus, details: str | None = None) -> None:
    AuditLog.create(
        telegram_id=telegram_id or 0,
        user_name="oauth_callback",
        command=_AUDIT_COMMAND,
        status=status,
        details=details,
    )


def _error_response(reason: str) -> HTMLResponse:
    return HTMLResponse(f"Gmail connection failed.<br>{reason}", status_code=400)
