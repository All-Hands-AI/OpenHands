import json
import os
import random
import shutil
import stat
import time
from dataclasses import dataclass, field

import pytest
from pytest import TempPathFactory

from openhands.core.config import AppConfig, MCPConfig, load_app_config
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.base import Runtime
from openhands.runtime.impl.daytona.daytona_runtime import DaytonaRuntime
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime
from openhands.runtime.impl.runloop.runloop_runtime import RunloopRuntime
from openhands.runtime.plugins import AgentSkillsRequirement, JupyterRequirement
from openhands.storage import get_file_store
from openhands.utils.async_utils import GENERAL_TIMEOUT, call_async_from_sync

TEST_IN_CI = os.getenv('TEST_IN_CI', 'False').lower() in ['true', '1', 'yes']
TEST_RUNTIME = os.getenv('TEST_RUNTIME', 'docker').lower()
RUN_AS_OPENHANDS = os.getenv('RUN_AS_OPENHANDS', 'True').lower() in ['true', '1', 'yes']
test_mount_path = ''
project_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sandbox_test_folder = '/workspace'


def _remove_folder(folder: str) -> bool:
    success = False
    if folder and os.path.isdir(folder):
        try:
            os.rmdir(folder)
            success = True
        except OSError:
            try:
                shutil.rmtree(folder)
                success = True
            except OSError:
                pass
        logger.debug(f'\nCleanup: `{folder}`: ' + ('[OK]' if success else '[FAILED]'))
    return success


def _close_test_runtime(runtime: Runtime) -> None:
    if isinstance(runtime, DockerRuntime):
        runtime.close(rm_all_containers=False)
    else:
        runtime.close()
    call_async_from_sync(runtime.__class__.delete, GENERAL_TIMEOUT, runtime.sid)
    time.sleep(1)


def _reset_cwd() -> None:
    global project_dir
    # Try to change back to project directory
    try:
        os.chdir(project_dir)
        logger.info(f'Changed back to project directory `{project_dir}')
    except Exception as e:
        logger.error(f'Failed to change back to project directory: {e}')


# *****************************************************************************
# *****************************************************************************


@pytest.fixture(autouse=True)
def print_method_name(request):
    print(
        '\n\n########################################################################'
    )
    print(f'Running test: {request.node.name}')
    print(
        '########################################################################\n\n'
    )


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory, request) -> str:
    """Creates a unique temporary directory.

    Upon finalization, the temporary directory and its content is removed.
    The cleanup function is also called upon KeyboardInterrupt.

    Parameters:
    - tmp_path_factory (TempPathFactory): A TempPathFactory class

    Returns:
    - str: The temporary directory path that was created
    """
    temp_dir = tmp_path_factory.mktemp(
        'rt_' + str(random.randint(100000, 999999)), numbered=False
    )

    logger.info(f'\n*** {request.node.name}\n>> temp folder: {temp_dir}\n')

    # Set permissions to ensure the directory is writable and deletable
    os.chmod(temp_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777 permissions

    def cleanup():
        global project_dir
        os.chdir(project_dir)
        _remove_folder(temp_dir)

    request.addfinalizer(cleanup)

    return str(temp_dir)


# Depending on TEST_RUNTIME, feed the appropriate box class(es) to the test.
def get_runtime_classes() -> list[type[Runtime]]:
    runtime = TEST_RUNTIME
    if runtime.lower() == 'docker' or runtime.lower() == 'eventstream':
        return [DockerRuntime]
    elif runtime.lower() == 'local':
        return [LocalRuntime]
    elif runtime.lower() == 'remote':
        return [RemoteRuntime]
    elif runtime.lower() == 'runloop':
        return [RunloopRuntime]
    elif runtime.lower() == 'daytona':
        return [DaytonaRuntime]
    else:
        raise ValueError(f'Invalid runtime: {runtime}')


def get_run_as_openhands() -> list[bool]:
    print(
        '\n\n########################################################################'
    )
    print('USER: ' + 'openhands' if RUN_AS_OPENHANDS else 'root')
    print(
        '########################################################################\n\n'
    )
    return [RUN_AS_OPENHANDS]


@pytest.fixture(scope='module')  # for xdist
def runtime_setup_module():
    _reset_cwd()
    yield
    _reset_cwd()


@pytest.fixture(scope='session')  # not for xdist
def runtime_setup_session():
    _reset_cwd()
    yield
    _reset_cwd()


# This assures that all tests run together per runtime, not alternating between them,
# which cause errors (especially outside GitHub actions).
@pytest.fixture(scope='module', params=get_runtime_classes())
def runtime_cls(request):
    time.sleep(1)
    return request.param


# TODO: We will change this to `run_as_user` when `ServerRuntime` is deprecated.
# since `DockerRuntime` supports running as an arbitrary user.
@pytest.fixture(scope='module', params=get_run_as_openhands())
def run_as_openhands(request):
    time.sleep(1)
    return request.param


@pytest.fixture(scope='module', params=None)
def base_container_image(request):
    time.sleep(1)
    env_image = os.environ.get('SANDBOX_BASE_CONTAINER_IMAGE')
    if env_image:
        request.param = env_image
    else:
        if not hasattr(request, 'param'):  # prevent runtime AttributeError
            request.param = None
        if request.param is None and hasattr(request.config, 'sandbox'):
            try:
                request.param = request.config.sandbox.getoption(
                    '--base_container_image'
                )
            except ValueError:
                request.param = None
        if request.param is None:
            request.param = pytest.param(
                'nikolaik/python-nodejs:python3.12-nodejs22',
                'golang:1.23-bookworm',
            )
    print(f'Container image: {request.param}')
    return request.param


def get_runtime_key(
    run_as_openhands: bool = True,
    enable_auto_lint: bool = False,
    base_container_image: str | None = None,
    browsergym_eval_env: str | None = None,
    use_workspace: bool | None = None,
    force_rebuild_runtime: bool = False,
    runtime_startup_env_vars: dict[str, str] | None = None,
    docker_runtime_kwargs: dict[str, str] | None = None,
    override_mcp_config: MCPConfig | None = None,
) -> str:
    return json.dumps(
        [
            run_as_openhands,
            enable_auto_lint,
            base_container_image,
            browsergym_eval_env,
            use_workspace,
            force_rebuild_runtime,
            runtime_startup_env_vars,
            docker_runtime_kwargs,
            override_mcp_config.model_dump() if override_mcp_config else None,
        ]
    )


@dataclass
class RuntimeManager:
    tmp_path_factory: TempPathFactory
    node_name: str
    runtime_cls: type
    runtimes: dict[str, tuple[Runtime, AppConfig]] = field(default_factory=dict)

    def __enter__(self):
        return self

    def load_runtime(
        self,
        run_as_openhands: bool = True,
        enable_auto_lint: bool = False,
        base_container_image: str | None = None,
        browsergym_eval_env: str | None = None,
        use_workspace: bool | None = None,
        force_rebuild_runtime: bool = False,
        runtime_startup_env_vars: dict[str, str] | None = None,
        docker_runtime_kwargs: dict[str, str] | None = None,
        override_mcp_config: MCPConfig | None = None,
    ):
        key = get_runtime_key(
            run_as_openhands,
            enable_auto_lint,
            base_container_image,
            browsergym_eval_env,
            use_workspace,
            force_rebuild_runtime,
            runtime_startup_env_vars,
            docker_runtime_kwargs,
            override_mcp_config,
        )
        result = self.runtimes.get(key)
        if result:
            return result
        temp_dir = self.tmp_path_factory.mktemp(
            'rt_' + str(random.randint(100000, 999999)), numbered=False
        )
        logger.info(f'\n*** {self.node_name}\n>> temp folder: {temp_dir}\n')
        result = _create_runtime(
            temp_dir,
            self.runtime_cls,
            run_as_openhands,
            enable_auto_lint,
            base_container_image,
            browsergym_eval_env,
            use_workspace,
            force_rebuild_runtime,
            runtime_startup_env_vars,
            docker_runtime_kwargs,
            override_mcp_config,
        )
        self.runtimes[key] = result
        return result

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close all runtimes"""
        for runtime, _ in self.runtimes.values():
            try:
                _close_test_runtime(runtime)
            except Exception as e:
                logger.error(e, exc_info=True, stack_info=True)


@pytest.fixture(scope='module')
def runtime_manager(runtime_cls, tmp_path_factory: TempPathFactory, request):
    with RuntimeManager(
        runtime_cls=runtime_cls,
        tmp_path_factory=tmp_path_factory,
        node_name=request.node.name,
    ) as runtime_manager:
        yield runtime_manager


def _create_runtime(
    temp_dir,
    runtime_cls,
    run_as_openhands: bool = True,
    enable_auto_lint: bool = False,
    base_container_image: str | None = None,
    browsergym_eval_env: str | None = None,
    use_workspace: bool | None = None,
    force_rebuild_runtime: bool = False,
    runtime_startup_env_vars: dict[str, str] | None = None,
    docker_runtime_kwargs: dict[str, str] | None = None,
    override_mcp_config: MCPConfig | None = None,
) -> tuple[Runtime, AppConfig]:
    sid = 'rt_' + str(random.randint(100000, 999999))

    # AgentSkills need to be initialized **before** Jupyter
    # otherwise Jupyter will not access the proper dependencies installed by AgentSkills
    plugins = [AgentSkillsRequirement(), JupyterRequirement()]

    config = load_app_config()
    config.run_as_openhands = run_as_openhands
    config.sandbox.force_rebuild_runtime = force_rebuild_runtime
    config.sandbox.keep_runtime_alive = False
    config.sandbox.docker_runtime_kwargs = docker_runtime_kwargs
    # Folder where all tests create their own folder
    global test_mount_path
    if use_workspace:
        test_mount_path = os.path.join(config.workspace_base, 'rt')
    elif temp_dir is not None:
        test_mount_path = temp_dir
    else:
        test_mount_path = None
    config.workspace_base = test_mount_path
    config.workspace_mount_path = test_mount_path

    # Mounting folder specific for this test inside the sandbox
    config.workspace_mount_path_in_sandbox = f'{sandbox_test_folder}'
    print('\nPaths used:')
    print(f'use_host_network: {config.sandbox.use_host_network}')
    print(f'workspace_base: {config.workspace_base}')
    print(f'workspace_mount_path: {config.workspace_mount_path}')
    print(
        f'workspace_mount_path_in_sandbox: {config.workspace_mount_path_in_sandbox}\n'
    )

    config.sandbox.browsergym_eval_env = browsergym_eval_env
    config.sandbox.enable_auto_lint = enable_auto_lint
    if runtime_startup_env_vars is not None:
        config.sandbox.runtime_startup_env_vars = runtime_startup_env_vars

    if base_container_image is not None:
        config.sandbox.base_container_image = base_container_image
        config.sandbox.runtime_container_image = None

    if override_mcp_config is not None:
        config.mcp = override_mcp_config

    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(sid, file_store)

    runtime = runtime_cls(
        config=config,
        event_stream=event_stream,
        sid=sid,
        plugins=plugins,
    )
    call_async_from_sync(runtime.connect)
    time.sleep(2)
    return runtime, config
