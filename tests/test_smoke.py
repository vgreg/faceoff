"""Smoke tests verifying the package imports correctly."""

import httpx

from faceoff import __version__
from faceoff.api import NHLClient
from faceoff.app import FaceoffApp


def test_version_is_string() -> None:
    assert isinstance(__version__, str)
    assert __version__


def test_nhl_client_uses_async_http() -> None:
    client = NHLClient()
    assert isinstance(client._http, httpx.AsyncClient)


def test_app_accepts_refresh_interval() -> None:
    app = FaceoffApp(refresh_interval=15)
    assert app.refresh_interval == 15
