"""HTTP callback entrypoint for Gmail OAuth."""

import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.integrations.gmail.exceptions import GmailOAuthError
from src.integrations.gmail.oauth_callback import GmailOAuthCallbackService
from src.integrations.gmail.settings import GmailOAuthSettings

LOGGER = logging.getLogger(__name__)
router = APIRouter()


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
        return _error_response(str(exc))
    except Exception:
        LOGGER.exception("Callback processing failed")
        return _error_response("Internal callback error.")

    if result.ok:
        return HTMLResponse("Gmail successfully connected.<br>You may close this browser window.")

    return _error_response(result.message)


def _error_response(reason: str) -> HTMLResponse:
    return HTMLResponse(f"Gmail connection failed.<br>{reason}", status_code=400)
