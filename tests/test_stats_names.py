"""Player names may be localized objects or plain strings; both must work."""

from faceoff.screens.stats import player_display_name


def test_localized_name_objects() -> None:
    player = {
        "firstName": {"default": "John"},
        "lastName": {"default": "Doe"},
    }
    assert player_display_name(player) == "J. Doe"


def test_plain_string_names() -> None:
    player = {"firstName": "John", "lastName": "Doe"}
    assert player_display_name(player) == "J. Doe"


def test_missing_names() -> None:
    assert player_display_name({}) == ""
