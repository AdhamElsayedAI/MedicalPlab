import pytest

@pytest.fixture(autouse=True)
def enable_phase_2b_by_default_in_remediation_tests(monkeypatch):
    """Enable Phase 2B by default inside tests/remediation/ so API tests can execute without manual flag boilerplate.
    Tests specifically asserting disabled behavior can override with monkeypatch.setenv('MEDICALPLAB_PHASE_2B_ENABLED', 'false').
    """
    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "true")
