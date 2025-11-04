"""
System Health Monitor

Monitors system health and quality metrics:
- Test status
- Build status
- Code quality
- Dependencies
- Security vulnerabilities
"""

import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from openhands.autonomous.perception.base import (
    BaseMonitor,
    EventPriority,
    EventType,
    PerceptionEvent,
)

logger = logging.getLogger(__name__)


class HealthMonitor(BaseMonitor):
    """
    Monitors system health

    Checks:
    - Test results
    - Build status
    - Dependency updates
    - Security vulnerabilities
    """

    def __init__(
        self,
        repo_path: str,
        check_interval: int = 600,  # 10 minutes
        run_tests: bool = True,
        check_dependencies: bool = True,
    ):
        """
        Args:
            repo_path: Path to repository
            check_interval: Check interval in seconds
            run_tests: Whether to run tests
            check_dependencies: Whether to check dependencies
        """
        super().__init__(name="HealthMonitor", check_interval=check_interval)

        self.repo_path = Path(repo_path)
        self.run_tests = run_tests
        self.check_dependencies = check_dependencies

        # State
        self.last_test_status: Optional[bool] = None
        self.last_build_status: Optional[bool] = None

    async def check(self) -> List[PerceptionEvent]:
        """Check system health"""
        events = []

        # Check tests
        if self.run_tests:
            test_events = await self._check_tests()
            events.extend(test_events)

        # Check build
        build_events = await self._check_build()
        events.extend(build_events)

        # Check dependencies
        if self.check_dependencies:
            dep_events = await self._check_dependencies()
            events.extend(dep_events)

        return events

    async def _run_command(self, command: List[str], timeout: int = 300) -> tuple[bool, str]:
        """
        Run a command and return (success, output)

        Args:
            command: Command to run
            timeout: Timeout in seconds

        Returns:
            (success, output)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_path),
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                output = stdout.decode() + stderr.decode()
                success = process.returncode == 0
                return success, output
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return False, "Command timeout"

        except Exception as e:
            logger.error(f"Failed to run command {' '.join(command)}: {e}")
            return False, str(e)

    async def _check_tests(self) -> List[PerceptionEvent]:
        """Check test status"""
        events = []

        # Determine test command based on what's available
        test_command = None

        if (self.repo_path / 'pytest.ini').exists() or (self.repo_path / 'setup.py').exists():
            test_command = ['pytest', '-v']
        elif (self.repo_path / 'package.json').exists():
            test_command = ['npm', 'test']
        elif (self.repo_path / 'Makefile').exists():
            test_command = ['make', 'test']

        if not test_command:
            logger.debug("No test framework detected")
            return events

        # Run tests
        logger.info("Running tests...")
        success, output = await self._run_command(test_command)

        # Check if status changed
        if self.last_test_status is not None and success != self.last_test_status:
            if success:
                # Tests now passing
                events.append(
                    PerceptionEvent(
                        event_type=EventType.TEST_PASSED,
                        priority=EventPriority.MEDIUM,
                        timestamp=datetime.now(),
                        source=self.name,
                        data={'output': output[:1000]},  # Limit output size
                    )
                )
                logger.info("Tests are now passing")
            else:
                # Tests now failing
                events.append(
                    PerceptionEvent(
                        event_type=EventType.TEST_FAILED,
                        priority=EventPriority.HIGH,
                        timestamp=datetime.now(),
                        source=self.name,
                        data={
                            'output': output[:1000],
                            'command': ' '.join(test_command),
                        },
                    )
                )
                logger.warning("Tests are now failing")

        self.last_test_status = success

        return events

    async def _check_build(self) -> List[PerceptionEvent]:
        """Check build status"""
        events = []

        # Determine build command
        build_command = None

        if (self.repo_path / 'setup.py').exists():
            build_command = ['python', 'setup.py', 'build']
        elif (self.repo_path / 'package.json').exists():
            build_command = ['npm', 'run', 'build']
        elif (self.repo_path / 'Dockerfile').exists():
            build_command = ['docker', 'build', '-t', 'test-build', '.']
        elif (self.repo_path / 'Makefile').exists():
            build_command = ['make', 'build']

        if not build_command:
            logger.debug("No build system detected")
            return events

        # Run build
        logger.info("Running build...")
        success, output = await self._run_command(build_command, timeout=600)

        # Check if status changed
        if self.last_build_status is not None and success != self.last_build_status:
            if success:
                events.append(
                    PerceptionEvent(
                        event_type=EventType.BUILD_SUCCEEDED,
                        priority=EventPriority.MEDIUM,
                        timestamp=datetime.now(),
                        source=self.name,
                        data={'output': output[:1000]},
                    )
                )
                logger.info("Build succeeded")
            else:
                events.append(
                    PerceptionEvent(
                        event_type=EventType.BUILD_FAILED,
                        priority=EventPriority.CRITICAL,
                        timestamp=datetime.now(),
                        source=self.name,
                        data={
                            'output': output[:1000],
                            'command': ' '.join(build_command),
                        },
                    )
                )
                logger.error("Build failed")

        self.last_build_status = success

        return events

    async def _check_dependencies(self) -> List[PerceptionEvent]:
        """Check for outdated dependencies"""
        events = []

        # Check Python dependencies
        if (self.repo_path / 'requirements.txt').exists():
            success, output = await self._run_command(['pip', 'list', '--outdated'])
            if success and output.strip():
                # Parse outdated packages
                lines = output.split('\n')[2:]  # Skip header
                outdated_packages = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            outdated_packages.append({
                                'name': parts[0],
                                'current': parts[1],
                                'latest': parts[2],
                            })

                if outdated_packages:
                    events.append(
                        PerceptionEvent(
                            event_type=EventType.DEPENDENCY_OUTDATED,
                            priority=EventPriority.MEDIUM,
                            timestamp=datetime.now(),
                            source=self.name,
                            data={
                                'count': len(outdated_packages),
                                'packages': outdated_packages[:10],  # Limit to 10
                            },
                        )
                    )
                    logger.info(f"Found {len(outdated_packages)} outdated Python packages")

        # Check npm dependencies
        elif (self.repo_path / 'package.json').exists():
            success, output = await self._run_command(['npm', 'outdated', '--json'])
            if success and output.strip():
                # npm outdated outputs JSON
                import json
                try:
                    outdated = json.loads(output)
                    if outdated:
                        events.append(
                            PerceptionEvent(
                                event_type=EventType.DEPENDENCY_OUTDATED,
                                priority=EventPriority.MEDIUM,
                                timestamp=datetime.now(),
                                source=self.name,
                                data={
                                    'count': len(outdated),
                                    'packages': list(outdated.keys())[:10],
                                },
                            )
                        )
                        logger.info(f"Found {len(outdated)} outdated npm packages")
                except json.JSONDecodeError:
                    pass

        return events
