"""Unit tests for the password service (hashing + strength rules)."""
import pytest

from app.modules.auth.services.password_service import password_service
from app.modules.auth.utils.exceptions import ValidationError


def test_hash_and_verify_roundtrip():
    h = password_service.hash("Str0ng!Pass")
    assert h != "Str0ng!Pass"
    assert password_service.verify("Str0ng!Pass", h) is True
    assert password_service.verify("wrong", h) is False


def test_verify_none_hash_is_false():
    assert password_service.verify("anything", None) is False


@pytest.mark.parametrize(
    "weak",
    ["Sh0rt!", "alllowercase1!", "ALLUPPERCASE1!", "NoNumber!!", "NoSpecial123"],
)
def test_weak_passwords_rejected(weak):
    with pytest.raises(ValidationError):
        password_service.validate_strength(weak)


def test_strong_password_accepted():
    password_service.validate_strength("Str0ng!Passw0rd")
