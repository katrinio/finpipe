import pytest

from src.services.profile_template.exceptions import InvalidProfileTemplateError
from src.services.profile_template.profile_template_validator import ProfileTemplateValidator


def test_validate_yaml_structure_accepts_valid_yaml() -> None:
    ProfileTemplateValidator.validate_yaml_structure(
        b"""
company_name: Test Company
company_address: Belgrade
""",
    )


def test_validate_yaml_structure_rejects_invalid_yaml() -> None:
    with pytest.raises(InvalidProfileTemplateError):
        ProfileTemplateValidator.validate_yaml_structure(b"company_name: [broken")


def test_validate_yaml_structure_rejects_empty_yaml() -> None:
    with pytest.raises(InvalidProfileTemplateError):
        ProfileTemplateValidator.validate_yaml_structure(b"")
