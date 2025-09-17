# python
import re
import time
from pathlib import Path

import pytest

CHECKLIST_PATH = Path("docs/UNSPLASH_PRODUCTION_CHECKLIST.md")


def _read_checklist_text():
    assert CHECKLIST_PATH.exists(), f"Checklist file not found at {CHECKLIST_PATH}"
    text = CHECKLIST_PATH.read_text(encoding="utf-8")
    return text


def test_file_exists_and_readable():
    """File should exist and be readable."""
    text = _read_checklist_text()
    assert len(text) > 0, "Checklist file is empty"


def test_contains_core_endpoints_and_helpers():
    """Checklist should reference the server endpoints and helper modules."""
    text = _read_checklist_text().lower()
    assert "post /internal/photos/track" in text or "/internal/photos/track" in text, "Missing /internal/photos/track reference"
    assert "get /internal/photos/meta" in text or "/internal/photos/meta" in text, "Missing /internal/photos/meta reference"
    # file paths (case-insensitive)
    assert "backend/services/unsplash_integration.py" in text, "Missing backend helper path reference"
    assert "backend/routers/unsplash.py" in text, "Missing backend router path reference"
    # helper names
    assert "triggerdownload" in text or "trigger_download" in text or "triggerdownload()" in text, "Missing triggerDownload helper mention"
    assert "build_attribution_html" in text, "Missing build_attribution_html helper mention"


def test_download_tracking_marked_done():
    """Download tracking parent checklist and many of its child items should be marked completed."""
    raw = _read_checklist_text()
    # Find the Download Tracking section block
    download_block_match = re.search(r"[-*]\s+\[.?]\s+\*\*Download Tracking\*\*:(.*?)(?:\n\n|\Z)", raw, re.S)
    # If exact match not found, fall back to searching proximity
    if download_block_match:
        block = download_block_match.group(1)
    else:
        # fallback: take a few lines after the heading
        heading_idx = raw.lower().find("download tracking")
        assert heading_idx != -1, "Download Tracking heading not found"
        block = raw[heading_idx : heading_idx + 800]
    # Expect several checked items (the doc indicates many subitems were done)
    checked_count = len(re.findall(r"-\s*\[x\]", block, re.I))
    assert checked_count >= 3, f"Expected at least 3 checked items in Download Tracking block, found {checked_count}"


def test_attribution_and_hotlinking_snippets_present():
    """Verify the doc includes attribution and hotlinking guidance/snippets."""
    text = _read_checklist_text()
    assert "photo by" in text.lower(), "Attribution text 'Photo by' not found"
    assert "on unsplash" in text.lower(), "Attribution 'on Unsplash' not found"
    # Dart code indicators
    assert "cachednetworkimage" in text.lower() or "cachednetworkimage(" in text, "CachedNetworkImage snippet not found"
    assert "photo.urls.regular" in text or "photo.urls.small" in text, "photo.urls.regular/small not referenced"
    # example of tracking snippet
    assert "trackPhotoUsage" in text or "photo.links.downloadLocation" in text, "Download tracking example snippet missing"


def test_screenshot_requirements_listed():
    """The three required screenshot items should be present and enumerated."""
    text = _read_checklist_text().lower()
    assert "photo attribution example" in text, "Screenshot requirement: Photo Attribution Example missing"
    assert "app interface" in text, "Screenshot requirement: App Interface missing"
    assert "photo integration" in text, "Screenshot requirement: Photo Integration missing"


def test_no_embedded_client_key():
    """Conservative check: ensure no obvious Client-ID secret is embedded in the docs.
    Allows the environment variable name UNSPLASH_CLIENT_ID but rejects likely literal keys (20+ alnum chars).
    """
    text = _read_checklist_text()
    # Look for patterns like 'Client-ID <token>' where token is long (20+ alnum)
    leak_pattern = re.compile(r"Client-ID\s*[:=]?\s*([A-Za-z0-9_\-]{20,})")
    match = leak_pattern.search(text)
    assert match is None, "Potential embedded Client-ID detected in documentation; please remove secrets from repo"


def test_ci_secret_header_variable_present_and_well_formed():
    """Construct a short-lived CI secret header value for CI runs and assert it meets policy for use inside CI tests.
    This documents the approach and ensures test authors use a header rather than an actual external secret.
    """
    ts = int(time.time())
    ci_secret = f"CI-DOC-TEST-{ts}"
    # Basic sanity checks: not too long, contains tag, numeric timestamp present
    assert "CI-DOC-TEST-" in ci_secret
    assert len(ci_secret) < 80
    assert re.search(r"\d{9,}", ci_secret), "Timestamp missing in generated CI secret"
    # The test does not call external services; this value is safe to include in CI logs if necessary.
    # For completeness include an assertion that the repo checklist file mentions secrets management guidance
    text = _read_checklist_text().lower()
    assert "secrets" in text or "client-id" in text or "environment" in text, "Checklist should mention secrets or environment guidance"