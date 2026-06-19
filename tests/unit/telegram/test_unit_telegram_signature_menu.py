from src.integrations.telegram.ui.buttons import SignatureButtons
from src.integrations.telegram.ui.menu.profile_menu import build_profile_menu


def test_profile_menu_contains_signature_actions() -> None:
    menu = build_profile_menu()

    all_buttons = [btn for row in menu["inline_keyboard"] for btn in row]
    assert any(btn["callback_data"] == SignatureButtons.CB_UPLOAD for btn in all_buttons)
    assert any(btn["callback_data"] == SignatureButtons.CB_DELETE for btn in all_buttons)
    assert any(btn["callback_data"] == "nav:main" for btn in all_buttons)
