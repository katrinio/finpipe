from src.integrations.telegram.buttons import NavigationButtons, SignatureButtons
from src.integrations.telegram.ui.menu.profile_menu import build_profile_menu


def test_profile_menu_contains_signature_actions() -> None:
    menu = build_profile_menu()

    assert any(button["text"] == SignatureButtons.SIGNATURE_UPLOAD for row in menu["keyboard"] for button in row)
    assert any(button["text"] == SignatureButtons.SIGNATURE_DELETE for row in menu["keyboard"] for button in row)
    assert any(button["text"] == NavigationButtons.HOME for row in menu["keyboard"] for button in row)
