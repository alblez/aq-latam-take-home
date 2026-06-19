"""CORS origin regex construction."""

from __future__ import annotations

import re

from app.config import build_cors_origin_regex


def test_blank_origins_yield_none() -> None:
    assert build_cors_origin_regex("") is None
    assert build_cors_origin_regex("   ") is None


def test_literal_origin_is_anchored_and_escaped() -> None:
    pattern = build_cors_origin_regex("http://localhost:3000")
    assert pattern is not None
    assert re.fullmatch(pattern, "http://localhost:3000")
    assert not re.fullmatch(pattern, "http://localhost:3001")


def test_glob_origin_matches_subdomains() -> None:
    pattern = build_cors_origin_regex("https://*.vercel.app")
    assert pattern is not None
    assert re.match(pattern, "https://preview.vercel.app")


def test_multiple_origins_are_combined() -> None:
    pattern = build_cors_origin_regex("http://localhost:3000, https://app.example.com")
    assert pattern is not None
    assert re.match(pattern, "http://localhost:3000")
    assert re.match(pattern, "https://app.example.com")
