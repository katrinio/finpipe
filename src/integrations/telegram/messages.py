class CommonMessages:
    ...
    # ABOUT = "🤖 Finpipe MVP\n\nFeatures:\n• Invoice generation\n• Gmail integration\n• Telegram bot\n• SQLite storage\n\nVersion: 0.1"


class GmailMessages: ...


class SignatureMessages: ...


class InvoiceMessages: ...


class BotInfo(
    CommonMessages,
    GmailMessages,
    SignatureMessages,
    InvoiceMessages,
): ...
