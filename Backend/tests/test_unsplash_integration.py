from unittest.mock import Mock, patch

from Backend.services import unsplash_integration as ui


def test_build_attribution_html_minimal():
    photo = {
        "user": {
            "name": "Jane Doe",
            "links": {"html": "https://unsplash.com/@janedoe"},
        },
        "links": {"html": "https://unsplash.com/photos/xyz"},
    }

    html = ui.build_attribution_html(photo)
    assert "Jane Doe" in html
    assert "unsplash.com/@janedoe" in html
    assert "unsplash.com/photos/xyz" in html


@patch("Backend.services.unsplash_integration.requests.get")
def test_trigger_photo_download_success(mock_get):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    ok = ui.trigger_photo_download(
        "https://api.unsplash.com/photos/xyz/download", "FAKE_KEY"
    )
    assert ok is True
    mock_get.assert_called_once()


@patch("Backend.services.unsplash_integration.requests.get")
def test_trigger_photo_download_network_failure(mock_get):
    mock_get.side_effect = Exception("network error")

    ok = ui.trigger_photo_download(
        "https://api.unsplash.com/photos/xyz/download", "FAKE_KEY"
    )
    assert ok is False
