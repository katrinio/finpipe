from dataclasses import dataclass


@dataclass(frozen=True)
class BankEmail:
    subject: str
    sender: str
    date: str
    message_id: str
    thread_id: str
    # attachment_id: str
