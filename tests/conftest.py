"""
pytest configuration for Aura test suite.
Sets asyncio mode to auto for all async tests.
"""

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require GCP auth)"
    )
