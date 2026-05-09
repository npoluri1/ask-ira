import pytest

from src.streaming import ConnectionManager


@pytest.mark.asyncio
async def test_connection_manager():
    manager = ConnectionManager()
    assert manager is not None


def test_connection_manager_singleton():
    from src.streaming import manager
    assert isinstance(manager, ConnectionManager)
