"""HTTP client adapter for the acquisition layer.

Design note — *what we reuse from Scrapling and why*: Scrapling's value is its **adaptive
``Selector`` parser** (used throughout this app) and its **curl_cffi browser-impersonation**
fetch backend. We talk to ``curl_cffi`` directly here — the very same library Scrapling's
``Fetcher`` wraps — so we get TLS/browser fingerprint impersonation *without* importing
Scrapling's Playwright-coupled fetcher module (its import chain requires the browser stack).
This keeps the monitor runnable in lightweight CI/Docker environments. Scrapling's
Playwright-based ``StealthyFetcher`` remains available as a lazy, optional fallback for
JS/anti-bot-heavy sources.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from curl_cffi import requests as curl_requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from job_monitor.observability import get_logger

logger = get_logger("scrapers.http")

_DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class ScraperHTTPError(RuntimeError):
    """Raised for non-success HTTP responses or transport failures."""

    def __init__(self, url: str, status: Optional[int] = None, detail: str = "") -> None:
        self.url = url
        self.status = status
        super().__init__(f"HTTP error for {url} (status={status}): {detail}".strip())


class HttpClient:
    """Configured HTTP client using ``curl_cffi`` with browser impersonation + retries."""

    def __init__(
        self,
        *,
        timeout: int = 30,
        retries: int = 3,
        impersonate: str = "chrome",
        stealthy_headers: bool = True,  # kept for API symmetry / future use
        use_stealth_fallback: bool = False,
    ) -> None:
        self.timeout = timeout
        self.retries = max(1, retries)
        self.impersonate = impersonate
        self.use_stealth_fallback = use_stealth_fallback

    # ----------------------------------------------------------------- public helpers
    def get_text(self, url: str, *, headers: Optional[Mapping[str, str]] = None) -> str:
        """GET ``url`` and return the decoded body as text."""
        return self._fetch(url, headers=headers).text

    def get_bytes(self, url: str, *, headers: Optional[Mapping[str, str]] = None) -> bytes:
        """GET ``url`` and return the raw body bytes (used for RSS/XML parsing)."""
        return self._fetch(url, headers=headers).content

    def get_json(self, url: str, *, headers: Optional[Mapping[str, str]] = None) -> Any:
        """GET ``url`` and decode the body as JSON."""
        json_headers = {"Accept": "application/json", **(headers or {})}
        response = self._fetch(url, headers=json_headers)
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise ScraperHTTPError(url, detail=f"invalid JSON: {exc}") from exc

    # ----------------------------------------------------------------- core
    def _fetch(self, url: str, *, headers: Optional[Mapping[str, str]] = None) -> Any:
        merged = {**_DEFAULT_HEADERS, **(headers or {})}
        try:
            response = self._request_with_retries(url, merged)
        except Exception as exc:  # noqa: BLE001 - normalize all transport errors
            logger.warning("Fetch failed for %s: %s", url, exc)
            if self.use_stealth_fallback:
                return self._stealth_get(url, merged)
            raise ScraperHTTPError(url, detail=str(exc)) from exc

        if response.status_code >= 400:
            if self.use_stealth_fallback:
                return self._stealth_get(url, merged)
            raise ScraperHTTPError(url, status=response.status_code, detail="non-success status")
        return response

    def _request_with_retries(self, url: str, headers: Mapping[str, str]) -> Any:
        # Build a retrying call bound to this instance's retry count.
        @retry(
            stop=stop_after_attempt(self.retries),
            wait=wait_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception_type(curl_requests.RequestsError),
            reraise=True,
        )
        def _do() -> Any:
            return curl_requests.get(
                url,
                headers=dict(headers),
                timeout=self.timeout,
                impersonate=self.impersonate,
                allow_redirects=True,
            )

        return _do()

    # ----------------------------------------------------------------- stealth fallback
    def _stealth_get(self, url: str, headers: Mapping[str, str]) -> Any:
        """Optional Playwright-based fetch via Scrapling's ``StealthyFetcher`` (lazy import).

        Returns an object exposing ``.text``/``.content``/``.json()`` like the curl response.
        Raises :class:`ScraperHTTPError` when the browser stack is unavailable.
        """
        try:
            from scrapling.fetchers import StealthyFetcher
        except Exception as exc:  # noqa: BLE001 - browser stack not installed
            raise ScraperHTTPError(url, detail=f"stealth fallback unavailable: {exc}") from exc
        logger.info("Using stealth fallback for %s", url)
        try:
            page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
            return _StealthResponse(page)
        except Exception as exc:  # noqa: BLE001
            raise ScraperHTTPError(url, detail=f"stealth fetch failed: {exc}") from exc


class _StealthResponse:
    """Adapt a Scrapling browser ``Response`` to the curl-like interface used here."""

    def __init__(self, page: Any) -> None:
        self._page = page
        self.status_code = getattr(page, "status", 200)

    @property
    def content(self) -> bytes:
        return self._page.body

    @property
    def text(self) -> str:
        body = self._page.body
        return body.decode("utf-8", errors="ignore") if isinstance(body, bytes) else str(body)

    def json(self) -> Any:
        return json.loads(self.text)
