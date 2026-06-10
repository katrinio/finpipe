from src.integrations.gmail.gmail_oauth import GmailOAuth, GmailOAuthResult

# TODO(MEDIUM):
# Этот модуль оставлен только как совместимый alias для старых импортов.
# После завершения миграции все вызовы должны перейти на `src.integrations.gmail.gmail_oauth`, чтобы убрать дублирование OAuth entrypoint.
__all__ = ["GmailOAuth", "GmailOAuthResult"]
