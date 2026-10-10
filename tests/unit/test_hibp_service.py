"""DB-free unit tests for the HIBP k-anonymity range lookup service.

Covers:
- matching password -> returns the breach count
- non-matching password -> 0
- valid response parsing
- mixed valid/malformed response -> HIBPVerificationError
- invalid suffix (not 35 hex chars) -> HIBPVerificationError
- invalid count (non-integer) -> HIBPVerificationError
- negative count -> HIBPVerificationError
- network/API failures -> HIBPVerificationError
"""

import hashlib
from unittest import mock

import httpx
import pytest

from backend.app.services import hibp_service

# 35-char lowercase hex string that satisfies the HIBP range-response suffix
# contract and is reused across this module's tests.
_SUFFIX_35 = "0123456789abcdef0123456789abcdef012"


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self._text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "boom", request=httpx.Request("GET", "http://x"), response=self
            )

    @property
    def text(self) -> str:
        return self._text


class _FakeClient:
    """Minimal stand-in for httpx.Client that returns a configured response."""

    def __init__(self, text: str, status_code: int = 200):
        self._response = _FakeResponse(text, status_code)

    def get(self, url: str):
        return self._response

    def close(self) -> None:
        pass


def _sha1_upper(password: str) -> str:
    return hashlib.sha1(password.encode("utf-8")).hexdigest().upper()


def test_matching_password_returns_breach_count() -> None:
    password = "test-password-123"
    lookup_hash = _sha1_upper(password)
    suffix = lookup_hash[5:]
    count = 7

    client = _FakeClient(f"{suffix}:{count}")
    assert hibp_service.check_password_against_hibp(password, client=client) == count


def test_non_matching_password_returns_zero() -> None:
    password = "test-password-123"
    lookup_hash = _sha1_upper(password)
    actual_suffix = lookup_hash[5:]  # the password's real 35-char suffix
    # A deliberately different 35-char hex suffix (leading 35 chars of the hash).
    suffix = lookup_hash[:35]

    client = _FakeClient(f"{suffix}:12")
    assert hibp_service.check_password_against_hibp(password, client=client) == 0


def test_response_parsing_valid_lines() -> None:
    text = f"{_SUFFIX_35}:5\n{_SUFFIX_35.upper()}:12\n"
    assert hibp_service._parse_range_text(text) == {
        _SUFFIX_35: 5,
        _SUFFIX_35.upper(): 12,
    }


def test_mixed_valid_malformed_response_raises() -> None:
    client = _FakeClient(
        f"{_SUFFIX_35}:7\nnot-a-valid-line\n{_SUFFIX_35}:12"
    )
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_invalid_suffix_length_raises() -> None:
    client = _FakeClient("ABC12:5")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_invalid_suffix_characters_raises() -> None:
    # 35-char suffix whose final character 'G' is not a hexadecimal value.
    suffix = "0" * 34 + "G"
    client = _FakeClient(f"{suffix}:5")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)

def test_empty_response_rejected() -> None:
    client = _FakeClient("")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_signed_count_raises() -> None:
    suffix = _SUFFIX_35
    client = _FakeClient(f"{suffix}:+7")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_whitespace_padded_count_raises() -> None:
    suffix = _SUFFIX_35
    client = _FakeClient(f"{suffix}: 7")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_non_ascii_digit_count_raises() -> None:
    suffix = _SUFFIX_35
    # Arabic-Indic digit (U+0667), not an ASCII decimal digit.
    client = _FakeClient(f"{suffix}:٧")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_injected_client_not_closed_by_service() -> None:
    client = mock.Mock(spec=httpx.Client)
    client.get.return_value = _FakeResponse(f"{_SUFFIX_35}:7")
    try:
        hibp_service.check_password_against_hibp("password", client=client)
    finally:
        assert not client.close.called


def test_service_created_client_closed_on_success() -> None:
    mock_client = mock.Mock(spec=httpx.Client)
    mock_client.get.return_value = _FakeResponse(f"{_SUFFIX_35}:7")
    with mock.patch.object(hibp_service.httpx, "Client", return_value=mock_client):
        hibp_service.check_password_against_hibp("password")

    mock_client.close.assert_called_once()


def test_service_created_client_closed_on_failure() -> None:
    mock_client = mock.Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.ConnectError("connection failed")
    with mock.patch.object(hibp_service.httpx, "Client", return_value=mock_client):
        with pytest.raises(hibp_service.HIBPVerificationError):
            hibp_service.check_password_against_hibp("password")

    mock_client.close.assert_called_once()


def test_prefix_only_sent_upstream() -> None:
    password = "test-password-123"
    lookup_hash = _sha1_upper(password)
    prefix = lookup_hash[:5]  # only the first 5 hex characters
    expected_url = f"https://api.pwnedpasswords.com/range/{prefix}"

    recorded: dict[str, str] = {}

    def fake_get(url: str, **kwargs: object) -> _FakeResponse:
        recorded["url"] = url
        return _FakeResponse(f"{lookup_hash[5:]}:7")

    client = mock.Mock(spec=httpx.Client)
    client.get.side_effect = fake_get

    hibp_service.check_password_against_hibp(password, client=client)

    assert recorded["url"] == expected_url
    suffix = "0" * 34 + "G"
    client = _FakeClient(f"{suffix}:5")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_invalid_count_raises() -> None:
    suffix = _SUFFIX_35
    client = _FakeClient(f"{suffix}:abc")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_negative_count_raises() -> None:
    suffix = _SUFFIX_35
    client = _FakeClient(f"{suffix}:-1")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_malformed_response_raises() -> None:
    client = _FakeClient("this is not a HIBP response at all")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_http_error_raises_hibp_verification_error() -> None:
    client = mock.Mock(spec=httpx.Client)
    client.get.side_effect = httpx.HTTPStatusError(
        "503", request=httpx.Request("GET", "http://x"), response=_FakeResponse("ok", 503)
    )
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)


def test_network_failure_raises_hibp_verification_error() -> None:
    client = mock.Mock(spec=httpx.Client)
    client.get.side_effect = httpx.ConnectError("connection failed")
    with pytest.raises(hibp_service.HIBPVerificationError):
        hibp_service.check_password_against_hibp("password", client=client)
