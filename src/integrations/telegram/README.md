# Telegram integration

The Telegram integration polls Bot API updates, authorizes users, routes menu commands, accepts profile and signature uploads, and returns generated documents to the requesting chat.

The main user flow is `Documents` → `Invoice` → `Create invoice`. Generated delivery files are removed immediately after the Telegram delivery attempt.
