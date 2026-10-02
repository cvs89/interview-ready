import pytest

from app.core.rate_limit import default_rate_limiter


@pytest.fixture(autouse=True)
def reset_in_memory_rate_limiter():
    default_rate_limiter.reset_memory()
    yield
    default_rate_limiter.reset_memory()
