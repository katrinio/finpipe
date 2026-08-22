# Telegram integration

The Telegram integration polls Bot API updates, authorizes users, routes menu commands, accepts profile and signature uploads, and returns generated documents to the requesting chat.

The document menu provides Salary Invoice, Conversion Request, and Bank Transfer Confirmation workflows. Bank confirmation accepts its source PDF directly from Telegram; Conversion Request uses the amount extracted from the latest uploaded bank document. Generated delivery files and uploaded bank inputs are removed immediately after the Telegram delivery attempt.
