#!/usr/bin/env python3
"""test_async_http.py — Unit tests for AsyncHTTPClient"""
import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    import aiohttp
except ImportError:
    pytest.skip("aiohttp not installed", allow_module_level=True)

from async_http import AsyncHTTPClient, fetch_urls_concurrent


class TestAsyncHTTPClient:
    """Test AsyncHTTPClient class."""

    @pytest.mark.asyncio
    async def test_init(self) -> None:
        """Test AsyncHTTPClient initialization."""
        client = AsyncHTTPClient(timeout=15.0, max_retries=2)
        assert client.max_retries == 2
        assert client.backoff_factor == 0.5

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test AsyncHTTPClient context manager."""
        async with AsyncHTTPClient(timeout=10.0) as client:
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)

    @pytest.mark.asyncio
    async def test_backoff_delay(self) -> None:
        """Test exponential backoff calculation."""
        async with AsyncHTTPClient() as client:
            delay0 = await client._backoff_delay(0)
            delay1 = await client._backoff_delay(1)
            delay2 = await client._backoff_delay(2)

            assert 0 <= delay0 <= 1.5  # 0.5 * 2^0 + jitter
            assert 0 <= delay1 <= 2.5  # 0.5 * 2^1 + jitter
            assert 0 <= delay2 <= 4.5  # 0.5 * 2^2 + jitter
            assert delay0 <= delay1 <= delay2 or (delay0 + 1 > delay1)  # Roughly increasing

    @pytest.mark.asyncio
    async def test_fetch_json(self) -> None:
        """Test fetch_json method."""
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"key": "value"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        async with AsyncHTTPClient() as client:
            with patch.object(client, "get", return_value=mock_response):
                result = await client.fetch_json("http://example.com/api")
                assert result == {"key": "value"}
                mock_response.json.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_text(self) -> None:
        """Test fetch_text method."""
        mock_response = MagicMock()
        mock_response.text = AsyncMock(return_value="Hello, World!")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        async with AsyncHTTPClient() as client:
            with patch.object(client, "get", return_value=mock_response):
                result = await client.fetch_text("http://example.com/api")
                assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_fetch_bytes(self) -> None:
        """Test fetch_bytes method."""
        content = b"binary data"
        mock_response = MagicMock()
        mock_response.read = AsyncMock(return_value=content)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        async with AsyncHTTPClient() as client:
            with patch.object(client, "get", return_value=mock_response):
                result = await client.fetch_bytes("http://example.com/image.png")
                assert result == content

    @pytest.mark.asyncio
    async def test_get_without_context_raises(self) -> None:
        """Test that get() raises if not in context manager."""
        client = AsyncHTTPClient()
        with pytest.raises(RuntimeError, match="not initialized"):
            await client.get("http://example.com")

    @pytest.mark.asyncio
    async def test_post_without_context_raises(self) -> None:
        """Test that post() raises if not in context manager."""
        client = AsyncHTTPClient()
        with pytest.raises(RuntimeError, match="not initialized"):
            await client.post("http://example.com", json={"key": "value"})


class TestFetchUrlsConcurrent:
    """Test fetch_urls_concurrent function."""

    @pytest.mark.asyncio
    async def test_empty_urls(self) -> None:
        """Test with empty URL list."""
        results = []
        async for url, data, exc in fetch_urls_concurrent([]):
            results.append((url, data, exc))
        assert results == []

    @pytest.mark.asyncio
    async def test_single_url(self) -> None:
        """Test with single URL."""
        mock_data = {"result": "success"}

        async def mock_fetch_json(url: str) -> dict[str, Any]:
            return mock_data

        with patch("async_http.AsyncHTTPClient.fetch_json", side_effect=mock_fetch_json):
            results = []
            async for url, data, exc in fetch_urls_concurrent(["http://example.com"]):
                results.append((url, data, exc))

            assert len(results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
