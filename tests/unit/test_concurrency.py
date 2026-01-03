import asyncio
from unittest.mock import MagicMock, patch

import pytest

from fastreq import ParallelRequests


@pytest.mark.asyncio
async def test_concurrency_semaphore_initial_value() -> None:
    """Test that concurrency semaphore is initialized with correct value."""
    with patch("fastreq.client.ParallelRequests._execute_request") as mock_exec:
        mock_exec.return_value = {"status": "ok"}

        async with ParallelRequests(concurrency=5) as client:
            semaphore = client._concurrency_semaphore
            assert semaphore._value == 5


@pytest.mark.asyncio
async def test_concurrency_default_value() -> None:
    """Test that default concurrency is 20."""
    with patch("fastreq.client.ParallelRequests._execute_request") as mock_exec:
        mock_exec.return_value = {"status": "ok"}

        async with ParallelRequests() as client:
            assert client.concurrency == 20
            assert client._concurrency_semaphore._value == 20


@pytest.mark.asyncio
async def test_concurrency_custom_values() -> None:
    """Test various concurrency values."""
    with patch("fastreq.client.ParallelRequests._execute_request") as mock_exec:
        mock_exec.return_value = {"status": "ok"}

        for value in [1, 5, 10, 50, 100]:
            async with ParallelRequests(concurrency=value) as client:
                assert client.concurrency == value
                assert client._concurrency_semaphore._value == value


@pytest.mark.asyncio
async def test_concurrency_semaphore_is_asyncio_semaphore() -> None:
    """Test that the concurrency semaphore is an asyncio.Semaphore."""
    with patch("fastreq.client.ParallelRequests._execute_request") as mock_exec:
        mock_exec.return_value = {"status": "ok"}

        async with ParallelRequests(concurrency=5) as client:
            semaphore = client._concurrency_semaphore
            assert isinstance(semaphore, asyncio.Semaphore)


@pytest.mark.asyncio
async def test_concurrency_parameter_stored() -> None:
    """Test that concurrency parameter is stored correctly."""
    with patch("fastreq.client.ParallelRequests._execute_request") as mock_exec:
        mock_exec.return_value = {"status": "ok"}

        async with ParallelRequests(concurrency=7) as client:
            assert client.concurrency == 7
