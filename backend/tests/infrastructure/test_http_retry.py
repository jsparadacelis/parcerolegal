"""Tests for the shared HTTP retry helper used by the provider adapters."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests
import responses

from backend.app.domain.ports import ServiceBusyError
from backend.app.infrastructure.config import SERVICE_BUSY_RETRY_AFTER_SECONDS
from backend.app.infrastructure.http_retry import RetryPolicy, post_with_retries

_URL = "https://api.proveedor.test/v1/endpoint"


@pytest.fixture
def mock_http():
    with responses.RequestsMock() as r:
        yield r


@pytest.fixture
def sleep() -> MagicMock:
    return MagicMock()


@pytest.fixture
def policy() -> RetryPolicy:
    return RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_total_wait_seconds=10.0,
        retryable_statuses=frozenset({429, 503}),
    )


def _post(policy: RetryPolicy, sleep: MagicMock) -> requests.Response:
    return post_with_retries(_URL, payload={"a": 1}, headers={}, timeout=5, policy=policy, sleep=sleep)


class TestPostWithRetries:
    def test_returns_response_on_first_success(self, policy, sleep, mock_http):
        mock_http.add(responses.POST, _URL, json={"ok": True}, status=200)

        response = _post(policy, sleep)

        assert response.json() == {"ok": True}
        sleep.assert_not_called()

    def test_retries_retryable_status_then_succeeds(self, policy, sleep, mock_http):
        mock_http.add(responses.POST, _URL, status=503)
        mock_http.add(responses.POST, _URL, json={"ok": True}, status=200)

        response = _post(policy, sleep)

        assert response.status_code == 200
        assert len(mock_http.calls) == 2

    def test_uses_exponential_backoff_without_sleeping_after_last_attempt(self, policy, sleep, mock_http):
        for _ in range(3):
            mock_http.add(responses.POST, _URL, status=429)

        with pytest.raises(ServiceBusyError):
            _post(policy, sleep)

        assert [c.args[0] for c in sleep.call_args_list] == [1.0, 2.0]

    def test_honors_retry_after_header_in_seconds(self, policy, sleep, mock_http):
        mock_http.add(responses.POST, _URL, status=429, headers={"Retry-After": "3"})
        mock_http.add(responses.POST, _URL, json={"ok": True}, status=200)

        _post(policy, sleep)

        sleep.assert_called_once_with(3.0)

    @pytest.mark.parametrize("header_value", ["mañana", "Wed, 21 Oct 2026 07:28:00 GMT", "-5"])
    def test_falls_back_to_backoff_on_unusable_retry_after(self, policy, sleep, mock_http, header_value):
        mock_http.add(responses.POST, _URL, status=429, headers={"Retry-After": header_value})
        mock_http.add(responses.POST, _URL, json={"ok": True}, status=200)

        _post(policy, sleep)

        sleep.assert_called_once_with(1.0)

    def test_gives_up_immediately_when_retry_after_exceeds_budget(self, policy, sleep, mock_http):
        mock_http.add(responses.POST, _URL, status=429, headers={"Retry-After": "30"})

        with pytest.raises(ServiceBusyError) as exc_info:
            _post(policy, sleep)

        sleep.assert_not_called()
        assert len(mock_http.calls) == 1
        assert exc_info.value.retry_after_seconds == 30

    def test_stops_retrying_when_accumulated_wait_would_exceed_budget(self, sleep, mock_http):
        tight_policy = RetryPolicy(
            max_attempts=5,
            base_delay_seconds=2.0,
            max_total_wait_seconds=5.0,
            retryable_statuses=frozenset({429}),
        )
        mock_http.add(responses.POST, _URL, status=429)
        mock_http.add(responses.POST, _URL, status=429)

        with pytest.raises(ServiceBusyError):
            _post(tight_policy, sleep)

        # 2s + 4s > 5s: solo cabe la primera espera.
        assert [c.args[0] for c in sleep.call_args_list] == [2.0]
        assert len(mock_http.calls) == 2

    def test_busy_error_carries_provider_retry_after_rounded_up(self, policy, sleep, mock_http):
        for _ in range(3):
            mock_http.add(responses.POST, _URL, status=429, headers={"Retry-After": "1.2"})

        with pytest.raises(ServiceBusyError) as exc_info:
            _post(policy, sleep)

        assert exc_info.value.retry_after_seconds == 2

    def test_busy_error_uses_default_retry_after_without_header(self, policy, sleep, mock_http):
        for _ in range(3):
            mock_http.add(responses.POST, _URL, status=429)

        with pytest.raises(ServiceBusyError) as exc_info:
            _post(policy, sleep)

        assert exc_info.value.retry_after_seconds == SERVICE_BUSY_RETRY_AFTER_SECONDS

    def test_busy_error_message_does_not_leak_url(self, policy, sleep, mock_http):
        for _ in range(3):
            mock_http.add(responses.POST, _URL, status=429)

        with pytest.raises(ServiceBusyError) as exc_info:
            _post(policy, sleep)

        assert "http" not in str(exc_info.value)

    def test_raises_http_error_when_server_errors_persist(self, policy, sleep, mock_http):
        for _ in range(3):
            mock_http.add(responses.POST, _URL, status=503)

        with pytest.raises(requests.HTTPError):
            _post(policy, sleep)

        assert len(mock_http.calls) == 3

    def test_raises_immediately_on_non_retryable_status(self, policy, sleep, mock_http):
        mock_http.add(responses.POST, _URL, status=500)

        with pytest.raises(requests.HTTPError):
            _post(policy, sleep)

        assert len(mock_http.calls) == 1
        sleep.assert_not_called()
