"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def db_engine():
    """Create a test database engine"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create a test database session"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_settings():
    """Mock application settings"""
    from unittest.mock import MagicMock
    settings = MagicMock()
    settings.MONITORING_INTERVAL_SECONDS = 60
    settings.MONITORING_MAX_CONCURRENCY = 10
    settings.MONITOR_FAILURE_THRESHOLD = 3
    settings.SNMP_TIMEOUT = 5
    settings.SNMP_RETRIES = 2
    return settings
