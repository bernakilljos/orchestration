#!/usr/bin/env python3
"""async_http.py — aiohttp wrapper with timeout, retry, and backoff

Usage:
    import asyncio
    from lib.async_http import AsyncHTTPClient

    async def main():
        async with AsyncHTTPClient(timeout=10, max_retries=3) as client:
            response = await client.get("https://example.com")
            data = await response.json()

    asyncio.run(main())
"""
import asyncio
import logging
import random
from typing import Any, AsyncIterator, Optional

try:
    import aiohttp
except ImportError:
    raise ImportError("aiohttp is required. Install with: pip install aiohttp")

logger = logging.getLogger(__name__)


class AsyncHTTPClient:
    """Async HTTP client with retry, backoff, and timeout handling."""

    def __init__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        backoff_max: float = 60.0,
    ) -> None:
        """Initialize AsyncHTTPClient.

        Args:
            timeout: Request timeout in seconds (default 10s)
            max_retries: Maximum number of retries (default 3)
            backoff_factor: Exponential backoff multiplier (default 0.5)
            backoff_max: Maximum backoff delay in seconds (default 60s)
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.backoff_max = backoff_max
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "AsyncHTTPClient":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=aiohttp.TCPConnector(ssl=True, limit_per_host=5),
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            # Allow graceful shutdown
            await asyncio.sleep(0.25)

    async def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.backoff_factor * (2 ** attempt) + random.uniform(0, 1),
            self.backoff_max,
        )
        return delay

    async def get(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Perform GET request with retry.

        Args:
            url: URL to request
            headers: Optional HTTP headers
            **kwargs: Additional arguments for ClientSession.get()

        Returns:
            aiohttp ClientResponse

        Raises:
            aiohttp.ClientError: If all retries exhausted
        """
        if self.session is None:
            raise RuntimeError("AsyncHTTPClient not initialized. Use 'async with' context manager.")

        return await self._request("GET", url, headers=headers, **kwargs)

    async def post(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        json: Optional[dict[str, Any]] = None,
        data: Optional[bytes] = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Perform POST request with retry.

        Args:
            url: URL to request
            headers: Optional HTTP headers
            json: Optional JSON payload
            data: Optional binary payload
            **kwargs: Additional arguments for ClientSession.post()

        Returns:
            aiohttp ClientResponse

        Raises:
            aiohttp.ClientError: If all retries exhausted
        """
        if self.session is None:
            raise RuntimeError("AsyncHTTPClient not initialized. Use 'async with' context manager.")

        return await self._request(
            "POST",
            url,
            headers=headers,
            json=json,
            data=data,
            **kwargs,
        )

    async def _request(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Internal request method with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            headers: Optional HTTP headers
            **kwargs: Additional arguments for ClientSession request

        Returns:
            aiohttp ClientResponse

        Raises:
            aiohttp.ClientError: If all retries exhausted
        """
        if self.session is None:
            raise RuntimeError("AsyncHTTPClient not initialized.")

        headers = headers or {}
        headers.setdefault("User-Agent", "AsyncHTTPClient/1.0")

        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"[HTTP] {method} {url} (attempt {attempt + 1}/{self.max_retries})")
                response = await self.session.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                return response
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                logger.warning(
                    f"[HTTP] {method} {url} failed (attempt {attempt + 1}): {type(e).__name__}",
                )
                if attempt < self.max_retries - 1:
                    delay = await self._backoff_delay(attempt)
                    logger.debug(f"[HTTP] Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[HTTP] {method} {url} exhausted {self.max_retries} retries")

        raise last_exception or aiohttp.ClientError(f"Failed to request {url}")

    async def fetch_json(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Fetch JSON from URL with retry.

        Args:
            url: URL to request
            headers: Optional HTTP headers

        Returns:
            Parsed JSON dictionary

        Raises:
            aiohttp.ClientError: If request fails
            aiohttp.ContentTypeError: If response is not JSON
        """
        response = await self.get(url, headers=headers)
        async with response:
            return await response.json()  # type: ignore

    async def fetch_text(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> str:
        """Fetch text from URL with retry.

        Args:
            url: URL to request
            headers: Optional HTTP headers

        Returns:
            Response text

        Raises:
            aiohttp.ClientError: If request fails
        """
        response = await self.get(url, headers=headers)
        async with response:
            return await response.text()

    async def fetch_bytes(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> bytes:
        """Fetch binary content from URL with retry.

        Args:
            url: URL to request
            headers: Optional HTTP headers

        Returns:
            Response content as bytes

        Raises:
            aiohttp.ClientError: If request fails
        """
        response = await self.get(url, headers=headers)
        async with response:
            return await response.read()


async def fetch_urls_concurrent(
    urls: list[str],
    timeout: float = 10.0,
    max_concurrent: int = 5,
) -> AsyncIterator[tuple[str, Optional[dict[str, Any]], Optional[Exception]]]:
    """Fetch multiple URLs concurrently.

    Args:
        urls: List of URLs to fetch
        timeout: Request timeout in seconds
        max_concurrent: Maximum concurrent requests

    Yields:
        Tuples of (url, json_data, exception)
    """
    async with AsyncHTTPClient(timeout=timeout) as client:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_one(url: str) -> tuple[str, Optional[dict[str, Any]], Optional[Exception]]:
            async with semaphore:
                try:
                    data = await client.fetch_json(url)
                    return (url, data, None)
                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {e}")
                    return (url, None, e)

        tasks = [fetch_one(url) for url in urls]
        for coro in asyncio.as_completed(tasks):
            yield await coro
