"""
core/context_osint.py

Thin server-side wrapper around the Context.dev REST API (native HTTP, no SDK).

Endpoints used:
    GET  https://api.context.dev/v1/web/urls?domain=<domain>
    POST https://api.context.dev/v1/web/scrape   (formats: markdown only)

Both public methods return a plain string so a Telegram bot can format and
send it directly. Failures are returned as strings starting with "Error:".

Configuration:
    config.py must define CONTEXT_DEV_API_KEY (keep config.py out of git).
"""

from __future__ import annotations

import logging
import time
from typing import Optional
from urllib.parse import urlparse

import requests

from config import CONTEXT_DEV_API_KEY

logger = logging.getLogger(__name__)

BASE_URL = "https://api.context.dev/v1"

# Only these statuses are retried. 400 and everything else fail immediately.
RETRYABLE_STATUSES = frozenset({408, 429})

CONNECT_TIMEOUT = 10   # seconds
READ_TIMEOUT = 100     # seconds; the API's own default deadline is 90s
MAX_RETRY_DELAY = 30   # seconds; cap for Retry-After / backoff sleeps

NO_CONTENT = "No content found."

_STATUS_MESSAGES = {
    401: "Error: Context.dev API key is missing, invalid, or disabled.",
    402: "Error: Context.dev credits exhausted.",
    403: "Error: This API key or plan is not permitted to make this request.",
    408: "Error: Request to Context.dev timed out.",
    429: "Error: Rate limit reached. Please try again shortly.",
}


class ContextOSINT:
    """Minimal Context.dev client for domain mapping and Markdown scraping."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 2,
    ) -> None:
        key = (api_key or CONTEXT_DEV_API_KEY or "").strip()
        if not key:
            raise ValueError(
                "CONTEXT_DEV_API_KEY is not set. Define it in config.py "
                "(get a key at https://www.context.dev/dashboard/api-keys)."
            )

        self.max_retries = max(0, max_retries)
        self.headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._session = requests.Session()
        self._session.headers.update(self.headers)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def map_urls(self, domain: str, max_results: Optional[int] = None) -> str:
        """
        List URLs discovered on a domain (GET /web/urls?domain=...).

        Returns the URLs as a newline-separated string, "No content found."
        if none were discovered, or an "Error: ..." string.
        `max_results` optionally truncates the returned list client-side.
        """
        clean_domain = self._normalize_domain(domain)
        if not clean_domain:
            return "Error: Please provide a valid domain, e.g. stripe.com"

        resp, error = self._request("GET", "/web/urls", params={"domain": clean_domain})
        if error:
            return error
        if resp.status_code != 200:
            return self._error_from_response(resp)

        try:
            body = resp.json()
        except ValueError:
            logger.error("Context.dev returned non-JSON for /web/urls")
            return "Error: Failed to map domain."

        raw_urls = body.get("urls") if isinstance(body, dict) else None
        urls = self._extract_urls(raw_urls)
        if not urls:
            return NO_CONTENT

        total = len(urls)
        if max_results is not None and max_results > 0 and total > max_results:
            shown = urls[:max_results]
            return "\n".join(shown) + f"\n... and {total - max_results} more"
        return "\n".join(urls)

    def scrape_url(self, url: str) -> str:
        """
        Fetch a page as Markdown (POST /web/scrape, fresh fetch every time).

        Returns the Markdown, "No content found." if the page is empty, or an
        "Error: ..." string on failure or a partial result.
        """
        clean_url = self._normalize_url(url)
        if not clean_url:
            return "Error: Please provide a valid http(s) URL."

        payload = {
            "url": clean_url,
            "formats": {"markdown": True},
            "maxAgeMs": 0,
        }

        resp, error = self._request("POST", "/web/scrape", json=payload)
        if error:
            return error
        if resp.status_code != 200:
            return self._error_from_response(resp)

        try:
            body = resp.json()
        except ValueError:
            logger.error("Context.dev returned non-JSON for /web/scrape")
            return "Error: Failed to scrape."

        if not isinstance(body, dict):
            return "Error: Failed to scrape."

        request_id = body.get("request_id")

        # A 200 response can still carry a failed or incomplete output.
        if body.get("isPartial"):
            logger.warning("Partial scrape result (request_id=%s)", request_id)
            return "Error: Failed to scrape (partial result)."

        markdown = body.get("markdown") or {}
        if markdown.get("success") is not True:
            logger.warning(
                "Markdown output failed (error_code=%s, request_id=%s)",
                markdown.get("error_code"),
                request_id,
            )
            return "Error: Failed to scrape."

        content = markdown.get("data")
        if not isinstance(content, str) or not content.strip():
            return NO_CONTENT
        return content

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _request(self, method: str, path: str, **kwargs):
        """
        Send a request, retrying only on 408 and 429.

        Returns (response, None) when a response was received (any status),
        or (None, "Error: ...") on a network-level failure.
        """
        url = f"{BASE_URL}{path}"
        resp = None

        for attempt in range(self.max_retries + 1):
            try:
                resp = self._session.request(
                    method,
                    url,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                    **kwargs,
                )
            except requests.Timeout:
                logger.warning("Timed out calling Context.dev %s %s", method, path)
                return None, "Error: Request to Context.dev timed out."
            except requests.RequestException as exc:
                # Log the exception type only; never log headers or the key.
                logger.error("Network error calling Context.dev: %s", type(exc).__name__)
                return None, "Error: Could not reach Context.dev."

            if resp.status_code in RETRYABLE_STATUSES and attempt < self.max_retries:
                delay = self._retry_delay(resp, attempt)
                logger.warning(
                    "Context.dev returned %s; retrying in %.1fs (attempt %d/%d)",
                    resp.status_code,
                    delay,
                    attempt + 1,
                    self.max_retries,
                )
                time.sleep(delay)
                continue

            return resp, None

        return resp, None  # pragma: no cover - loop always returns above

    @staticmethod
    def _retry_delay(resp: requests.Response, attempt: int) -> float:
        """Honor Retry-After when present, else exponential backoff (1s, 2s, 4s...)."""
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return min(max(float(retry_after), 0.0), MAX_RETRY_DELAY)
            except ValueError:
                pass
        return min(float(2 ** attempt), MAX_RETRY_DELAY)

    @staticmethod
    def _error_from_response(resp: requests.Response) -> str:
        """Turn a non-200 response into a short, user-safe error string."""
        try:
            body = resp.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}

        logger.error(
            "Context.dev HTTP %s (error_code=%s, request_id=%s)",
            resp.status_code,
            body.get("error_code"),
            body.get("request_id"),
        )

        if resp.status_code == 400:
            detail = body.get("message")
            if detail:
                return f"Error: Invalid request ({detail})"
            return "Error: Invalid request."

        if resp.status_code in _STATUS_MESSAGES:
            return _STATUS_MESSAGES[resp.status_code]

        return f"Error: Context.dev returned HTTP {resp.status_code}."

    @staticmethod
    def _normalize_domain(raw: str) -> str:
        """Reduce user input like 'https://Stripe.com/docs' to 'stripe.com'."""
        raw = (raw or "").strip()
        if not raw or any(ch.isspace() for ch in raw):
            return ""
        try:
            parsed = urlparse(raw if "://" in raw else f"//{raw}")
            return (parsed.hostname or "").lower()
        except ValueError:
            return ""

    @staticmethod
    def _normalize_url(raw: str) -> str:
        """Ensure an http(s) URL; add https:// when the scheme is missing."""
        raw = (raw or "").strip()
        if not raw or any(ch.isspace() for ch in raw):
            return ""
        candidate = raw if "://" in raw else f"https://{raw}"
        try:
            parsed = urlparse(candidate)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                return ""
        except ValueError:
            return ""
        return candidate

    @staticmethod
    def _extract_urls(raw_urls) -> list[str]:
        """Accept a list of strings, or of objects carrying a 'url' field."""
        if not isinstance(raw_urls, list):
            return []
        urls: list[str] = []
        for item in raw_urls:
            if isinstance(item, str) and item:
                urls.append(item)
            elif isinstance(item, dict) and isinstance(item.get("url"), str):
                urls.append(item["url"])
        return urls


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # NOTE: this makes live API calls and consumes credits.
    client = ContextOSINT()

    print("=== map_urls('stripe.com') ===")
    mapped = client.map_urls("stripe.com", max_results=20)
    print(mapped)

    print("\n=== scrape_url('https://pib.gov.in') ===")
    scraped = client.scrape_url("https://pib.gov.in")
    print(scraped[:1500] + ("\n... [truncated]" if len(scraped) > 1500 else ""))
