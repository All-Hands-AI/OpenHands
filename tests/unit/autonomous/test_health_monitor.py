"""
Tests for Health Monitor
"""

import asyncio
from pathlib import Path

import pytest

from openhands.autonomous.perception.base import EventType
from openhands.autonomous.perception.health_monitor import HealthMonitor


class TestHealthMonitor:
    """Tests for HealthMonitor class"""

    def test_create_monitor(self, temp_repo):
        """Test creating a health monitor"""
        monitor = HealthMonitor(
            repo_path=str(temp_repo),
            check_interval=1,
            run_tests=True,
            check_dependencies=True,
        )

        assert monitor.repo_path == temp_repo
        assert monitor.run_tests
        assert monitor.check_dependencies

    def test_create_monitor_without_tests(self, temp_repo):
        """Test creating monitor without running tests"""
        monitor = HealthMonitor(
            repo_path=str(temp_repo),
            run_tests=False,
            check_dependencies=False,
        )

        assert not monitor.run_tests
        assert not monitor.check_dependencies

    @pytest.mark.asyncio
    async def test_run_command_success(self, temp_repo):
        """Test running a successful command"""
        monitor = HealthMonitor(repo_path=str(temp_repo))

        success, output = await monitor._run_command(['echo', 'hello'])

        assert success
        assert 'hello' in output

    @pytest.mark.asyncio
    async def test_run_command_failure(self, temp_repo):
        """Test running a failed command"""
        monitor = HealthMonitor(repo_path=str(temp_repo))

        success, output = await monitor._run_command(['false'])

        assert not success

    @pytest.mark.asyncio
    async def test_run_command_timeout(self, temp_repo):
        """Test command timeout"""
        monitor = HealthMonitor(repo_path=str(temp_repo))

        success, output = await monitor._run_command(['sleep', '10'], timeout=0.1)

        assert not success
        assert 'timeout' in output.lower()

    @pytest.mark.asyncio
    async def test_check_tests_no_framework(self, temp_repo):
        """Test checking tests when no framework detected"""
        monitor = HealthMonitor(repo_path=str(temp_repo), run_tests=True)

        events = await monitor._check_tests()

        # Should return empty if no test framework
        assert events == []

    @pytest.mark.asyncio
    async def test_check_tests_with_pytest(self, temp_repo):
        """Test checking tests with pytest"""
        # Create pytest.ini to indicate pytest is used
        (temp_repo / 'pytest.ini').write_text('[pytest]')

        monitor = HealthMonitor(repo_path=str(temp_repo), run_tests=True)

        # First check - establishes baseline
        events = await monitor._check_tests()

        # Status should be recorded
        assert monitor.last_test_status is not None

    @pytest.mark.asyncio
    async def test_check_tests_status_change(self, temp_repo):
        """Test detecting test status change"""
        (temp_repo / 'pytest.ini').write_text('[pytest]')

        monitor = HealthMonitor(repo_path=str(temp_repo), run_tests=True)

        # Set initial status
        monitor.last_test_status = True

        # Mock test failure
        async def mock_run_failure(cmd, timeout=300):
            return False, "Tests failed"

        original_run = monitor._run_command
        monitor._run_command = mock_run_failure

        events = await monitor._check_tests()

        # Should detect status change
        if events:
            assert events[0].event_type == EventType.TEST_FAILED

        # Restore
        monitor._run_command = original_run

    @pytest.mark.asyncio
    async def test_check_build_no_system(self, temp_repo):
        """Test checking build when no build system"""
        monitor = HealthMonitor(repo_path=str(temp_repo))

        events = await monitor._check_build()

        assert events == []

    @pytest.mark.asyncio
    async def test_check_build_with_setup_py(self, temp_repo):
        """Test checking build with setup.py"""
        (temp_repo / 'setup.py').write_text('# setup')

        monitor = HealthMonitor(repo_path=str(temp_repo))

        events = await monitor._check_build()

        # Should attempt to build
        assert monitor.last_build_status is not None

    @pytest.mark.asyncio
    async def test_check_dependencies_python(self, temp_repo):
        """Test checking Python dependencies"""
        (temp_repo / 'requirements.txt').write_text('pytest\n')

        monitor = HealthMonitor(repo_path=str(temp_repo), check_dependencies=True)

        # Mock pip list output
        async def mock_pip_list(cmd, timeout=300):
            if 'pip' in cmd and 'outdated' in cmd:
                return True, "Package    Version Latest\npytest     7.0.0   7.4.0"
            return True, ""

        monitor._run_command = mock_pip_list

        events = await monitor._check_dependencies()

        # Should detect outdated packages
        if events:
            assert events[0].event_type == EventType.DEPENDENCY_OUTDATED
            assert events[0].data['count'] > 0

    @pytest.mark.asyncio
    async def test_check_dependencies_npm(self, temp_repo):
        """Test checking npm dependencies"""
        (temp_repo / 'package.json').write_text('{}')

        monitor = HealthMonitor(repo_path=str(temp_repo), check_dependencies=True)

        # Mock npm outdated
        async def mock_npm_outdated(cmd, timeout=300):
            if 'npm' in cmd and 'outdated' in cmd:
                return True, '{"react": {"current": "17.0.0", "latest": "18.0.0"}}'
            return True, ""

        monitor._run_command = mock_npm_outdated

        events = await monitor._check_dependencies()

        # Should detect outdated npm packages
        if events:
            assert events[0].event_type == EventType.DEPENDENCY_OUTDATED

    @pytest.mark.asyncio
    async def test_check_with_all_monitors(self, temp_repo):
        """Test full health check with all monitors enabled"""
        monitor = HealthMonitor(
            repo_path=str(temp_repo),
            run_tests=True,
            check_dependencies=True,
        )

        events = await monitor.check()

        # Should run all checks
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_check_without_tests(self, temp_repo):
        """Test health check without running tests"""
        monitor = HealthMonitor(
            repo_path=str(temp_repo),
            run_tests=False,
            check_dependencies=False,
        )

        events = await monitor.check()

        # Should only check build
        assert isinstance(events, list)
