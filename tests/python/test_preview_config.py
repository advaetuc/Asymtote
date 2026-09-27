"""Offline preview-target checks; parsing must not make any remote requests."""

import urllib.request

import pytest

from scripts.verify_preview import parse_args


@pytest.fixture(autouse=True)
def forbid_network_and_clear_target(monkeypatch):
    monkeypatch.delenv("AUGMENTR_PREVIEW_URL", raising=False)
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *args, **kwargs: pytest.fail("No network allowed")
    )


def test_preview_defaults_to_augmentr_without_contacting_it():
    assert parse_args(["--output", "result.json"]).origin == "https://augmentr.vercel.app"


def test_explicit_origin_overrides_environment(monkeypatch):
    monkeypatch.setenv("AUGMENTR_PREVIEW_URL", "https://environment.example")
    assert (
        parse_args(["https://authorized.example/", "--output", "result.json"]).origin
        == "https://authorized.example"
    )


def test_environment_can_select_an_authorized_preview(monkeypatch):
    monkeypatch.setenv("AUGMENTR_PREVIEW_URL", "https://authorized.example/")
    assert parse_args(["--output", "result.json"]).origin == "https://authorized.example"


@pytest.mark.parametrize(
    "origin",
    [
        "",
        "http://augmentr.vercel.app",
        "https://user:password@augmentr.vercel.app",
        "https://augmentr.vercel.app/solve",
        "https://augmentr.vercel.app?query=value",
        "https://augmentr.vercel.app#fragment",
        "not-a-url",
    ],
)
def test_invalid_environment_target_is_rejected_before_requests(origin, monkeypatch):
    monkeypatch.setenv("AUGMENTR_PREVIEW_URL", origin)
    with pytest.raises(SystemExit) as error:
        parse_args(["--output", "result.json"])
    assert error.value.code == 2


def test_output_is_required_before_remote_verification_can_start():
    with pytest.raises(SystemExit) as error:
        parse_args([])
    assert error.value.code == 2
