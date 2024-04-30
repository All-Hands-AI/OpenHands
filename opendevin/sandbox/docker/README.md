# Use SWE-Bench Environment in the OpenDevin Sandbox

This README provides guidance on how to use the SWE-Bench environment within the OpenDevin sandbox. Note that this integration is actively being developed and may undergo changes.

Warning: we are in the process of dockerizing SWE-bench utility files, which are currently prepared and managed externally.

## Prerequisites

### Prepare SWE-Bench utilities

To set up, please utilize our modified version at [OD-SWE-bench/tree/eval](https://github.com/OpenDevin/OD-SWE-bench/tree/eval). Follow the [instructions](https://github.com/OpenDevin/OD-SWE-bench/blob/eval/swebench/harness/OD_README.md) to prepare both the testbeds and necessary conda environments for OD-SWE-Bench and SWE-Bench test instances.

To prevent any unintended modifications, the following components will be mounted in read-only (`ro`) mode in the sandbox:

- Testbeds for SWE-bench intances: They are located in `OD-SWE-bench/swebench/harness/eval_data/testbeds`. Each instance-specific testbed will be copied to the sandbox's workspace.
- Conda environments: Found in `YOUR_SYSTEM_CONDA_ENVS_DIR`, for example, `$HOME/miniconda3/envs`:
  - `swe-bench-eval`: Resets the testbed for a specific instance in the sandbox on the fly. This environment is cached at `/tmp/cache` on the host.
  - Instance specific environment (e.g., `django__django__3.0`): Each environment is where the agent operates to complete tasks within the sandbox. These are cloned directly into the sandbox using `conda create --clone`.
- OD-SWE-Bench repo: Manages the reset of testbeds for specific instances in the sandbox.

### Prepare cache

Mount the `/tmp/cache` directory within the sandbox by preparing it on the host using the following commands:

```shell
sudo cp PATH_TO_OD_SWE_bench/swebench/harness/eval_data/instances/swe-bench-test.json /tmp/cache
sudo wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/cache/Miniconda3-latest-Linux-x86_64.sh
```

## How it works

The script `swe_env_box.py` initially creates a sandbox and mounts necessary directories as follows:

```python
volumes={
    # mount workspace
    mount_dir: {
        'bind': SANDBOX_WORKSPACE_DIR,
        'mode': 'rw'
    },
    # mount cache directory to $HOME/.cache for pip cache reuse
    config.get(ConfigType.CACHE_DIR): {
        'bind': '$HOME/.cache',
        'mode': 'rw'
    },
    # mount OD-SWE-bench dir
    self.od_swe_bench_dir: {
        'bind': '/swe_util/OD-SWE-bench',
        'mode': 'ro'
    },
    # mount conda envs dir
    self.conda_envs_dir: {
        'bind': '/swe_util/conda_envs',
        'mode': 'ro'
    },
},
```

Subsequently, swe_env_setup.sh is run inside the sandbox to:

1. Install miniconda3
2. Clone `swe-bench-eval` environment
3. Read the `swe-bench-lite-test.json` file and extract the required item based on instance_id
4. Get instance-specific `CONDA_ENV_NAME` from the item
    1. Dump test patch to `/workspace/test.patch`
    2. Dump gold patch to `/workspace/gold.patch`
    3. Dump the item to `/workspace/instance.json` for further usage
5. Clone instance-specific environment
6. Copy instance-specific testbed (repo) to workspace
7. Reset the testbed and install the repo

## Interact with the SWE-bench environment

To interact within the SWE-Bench environment using `swe_env_box.py`, specify the following arguments:

- `swe_instance_id`: instance id
- `od_swe_bench_dir`: path to your OD-SWE-bench repo
- `conda_envs_dir`: path to your system conda environments

Follow the [document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to run OpenDevin in the developer mode and execute the following commands:

```shell
cd opendevin/sandbox/docker
python swe_env_box.py
```

When entering the sandbox interactively, execute these commands for a basic functionality check:

1. `conda activate django__django__3.0`: activates the instance-specific environment.
2. `cd /workspace/django__django__3.0`: navigate to the target repo.
3. `git apply -v ../test.patch`: apply the test patch.
4. `./tests/runtests.py --verbosity 2 auth_tests.test_validators`: run the tests, which are expected to fail initially.
5. `git apply ../gold.patch`: apply the gold patch.
6. `./tests/runtests.py --verbosity 2 auth_tests.test_validators`: run the tests again. This time, the tests should pass.

An example log for instance `django__django-11099` is shown below.

```shell
(opendevin-py3.11) (base) bowenl@iZt4n5pogo006xy6aozyylZ:/shared/bowen/codellm/swe/OpenDevin/opendevin/sandbox/docker$ python swe_env_box.py

20:56:00 - opendevin:INFO: swe_env_box.py:109 - Container stopped
20:56:00 - opendevin:WARNING: swe_env_box.py:121 - Using port forwarding for Mac OS. Server started by OpenDevin will not be accessible from the host machine at the moment. See https://github.com/OpenDevin/OpenDevin/issues/897 for more information.
20:56:00 - opendevin:INFO: swe_env_box.py:130 - Mounting workspace directory: /shared/bowen/codellm/swe/OpenDevin/opendevin/sandbox/docker
20:56:00 - opendevin:INFO: swe_env_box.py:157 - Container started
20:56:01 - opendevin:INFO: swe_env_box.py:174 - waiting for container to start: 1, container status: running
20:56:01 - opendevin:INFO: ssh_box.py:178 - Connecting to opendevin@localhost via ssh. If you encounter any issues, you can try `ssh -v -p 33523 opendevin@localhost` with the password '87beacba-3373-45af-aac2-29bb2368c65a' and report the issue on GitHub.
20:56:02 - opendevin:INFO: swe_env_box.py:90 - exit code: 0
20:56:02 - opendevin:INFO: swe_env_box.py:91 -
20:57:11 - opendevin:INFO: swe_env_box.py:94 - exit code: 0
Get:1 http://archive.ubuntu.com/ubuntu jammy InRelease [270 kB]
Get:2 http://security.ubuntu.com/ubuntu jammy-security InRelease [110 kB]
Get:3 http://security.ubuntu.com/ubuntu jammy-security/main amd64 Packages [1756 kB]
Get:4 http://archive.ubuntu.com/ubuntu jammy-updates InRelease [119 kB]
Get:5 http://security.ubuntu.com/ubuntu jammy-security/universe amd64 Packages [1077 kB]
Get:6 http://archive.ubuntu.com/ubuntu jammy-backports InRelease [109 kB]
Get:7 http://security.ubuntu.com/ubuntu jammy-security/restricted amd64 Packages [2265 kB]
Get:8 http://security.ubuntu.com/ubuntu jammy-security/multiverse amd64 Packages [44.7 kB]
Get:9 http://archive.ubuntu.com/ubuntu jammy/restricted amd64 Packages [164 kB]
Get:10 http://archive.ubuntu.com/ubuntu jammy/main amd64 Packages [1792 kB]
Get:11 http://archive.ubuntu.com/ubuntu jammy/universe amd64 Packages [17.5 MB]
Get:12 http://archive.ubuntu.com/ubuntu jammy/multiverse amd64 Packages [266 kB]
Get:13 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 Packages [2035 kB]
Get:14 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 Packages [1370 kB]
Get:15 http://archive.ubuntu.com/ubuntu jammy-updates/multiverse amd64 Packages [51.1 kB]
Get:16 http://archive.ubuntu.com/ubuntu jammy-updates/restricted amd64 Packages [2339 kB]
Get:17 http://archive.ubuntu.com/ubuntu jammy-backports/main amd64 Packages [81.0 kB]
Get:18 http://archive.ubuntu.com/ubuntu jammy-backports/universe amd64 Packages [31.9 kB]
Fetched 31.4 MB in 54s (585 kB/s)
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
build-essential is already the newest version (12.9ubuntu3).
The following additional packages will be installed:
  libpython3.11-minimal libpython3.11-stdlib python3.11-minimal
Suggested packages:
  python3.11-venv python3.11-doc binfmt-support
The following NEW packages will be installed:
  libffi-dev libpython3.11-minimal libpython3.11-stdlib python3.11
  python3.11-minimal
0 upgraded, 5 newly installed, 0 to remove and 4 not upgraded.
Need to get 5679 kB of archives.
After this operation, 21.8 MB of additional disk space will be used.
Get:1 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libpython3.11-minimal amd64 3.11.0~rc1-1~22.04 [837 kB]
Get:2 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3.11-minimal amd64 3.11.0~rc1-1~22.04 [2370 kB]
Get:3 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 libpython3.11-stdlib amd64 3.11.0~rc1-1~22.04 [1859 kB]
Get:4 http://archive.ubuntu.com/ubuntu jammy-updates/universe amd64 python3.11 amd64 3.11.0~rc1-1~22.04 [550 kB]
Get:5 http://archive.ubuntu.com/ubuntu jammy/main amd64 libffi-dev amd64 3.4.2-4 [63.7 kB]
Fetched 5679 kB in 6s (1028 kB/s)
debconf: delaying package configuration, since apt-utils is not installed
Selecting previously unselected package libpython3.11-minimal:amd64.
(Reading database ... 23851 files and directories currently installed.)
Preparing to unpack .../libpython3.11-minimal_3.11.0~rc1-1~22.04_amd64.deb ...
Unpacking libpython3.11-minimal:amd64 (3.11.0~rc1-1~22.04) ...
Selecting previously unselected package python3.11-minimal.
Preparing to unpack .../python3.11-minimal_3.11.0~rc1-1~22.04_amd64.deb ...
Unpacking python3.11-minimal (3.11.0~rc1-1~22.04) ...
Selecting previously unselected package libpython3.11-stdlib:amd64.
Preparing to unpack .../libpython3.11-stdlib_3.11.0~rc1-1~22.04_amd64.deb ...
Unpacking libpython3.11-stdlib:amd64 (3.11.0~rc1-1~22.04) ...
Selecting previously unselected package python3.11.
Preparing to unpack .../python3.11_3.11.0~rc1-1~22.04_amd64.deb ...
Unpacking python3.11 (3.11.0~rc1-1~22.04) ...
Selecting previously unselected package libffi-dev:amd64.
Preparing to unpack .../libffi-dev_3.4.2-4_amd64.deb ...
Unpacking libffi-dev:amd64 (3.4.2-4) ...
Setting up libffi-dev:amd64 (3.4.2-4) ...
Setting up libpython3.11-minimal:amd64 (3.11.0~rc1-1~22.04) ...
Setting up python3.11-minimal (3.11.0~rc1-1~22.04) ...
Setting up libpython3.11-stdlib:amd64 (3.11.0~rc1-1~22.04) ...
Setting up python3.11 (3.11.0~rc1-1~22.04) ...
SWEUTIL_DIR: /swe_util

......

20:57:11 - opendevin:INFO: swe_env_box.py:101 - Sourced ~/.bashrc successfully
20:57:11 - opendevin:INFO: swe_env_box.py:191 - Interactive Docker container started. Type 'exit' or use Ctrl+C to exit.

>>> conda activate django__django__3.0

20:57:22 - opendevin:INFO: swe_env_box.py:214 - exit code: 0
20:57:22 - opendevin:INFO: swe_env_box.py:215 -
20:57:22 - opendevin:INFO: swe_env_box.py:218 - background logs: dot
dot

>>> cd /workspace/django__django__3.0

20:57:26 - opendevin:INFO: swe_env_box.py:214 - exit code: 0
20:57:26 - opendevin:INFO: swe_env_box.py:215 -
20:57:26 - opendevin:INFO: swe_env_box.py:218 - background logs:

>>> git apply ../test.patch

20:57:47 - opendevin:INFO: swe_env_box.py:214 - exit code: 0
20:57:47 - opendevin:INFO: swe_env_box.py:215 -
20:57:47 - opendevin:INFO: swe_env_box.py:218 - background logs: dot

>>> ./tests/runtests.py --verbosity 2 auth_tests.test_validators

20:57:49 - opendevin:INFO: swe_env_box.py:214 - exit code: 1
20:57:49 - opendevin:INFO: swe_env_box.py:215 - Testing against Django installed in '/workspace/django__django__3.0/django' with up to 64 processes
Importing application auth_tests
Skipping setup of unused database(s): other.
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Operations to perform:
  Synchronize unmigrated apps: auth, auth_tests, contenttypes, messages, sessions, staticfiles
  Apply all migrations: admin, sites
Synchronizing apps without migrations:
  Creating tables...
    Creating table django_content_type
    Creating table auth_permission
    Creating table auth_group
    Creating table auth_user
    Creating table django_session
    Creating table auth_tests_customuser
    Creating table auth_tests_customuserwithoutisactivefield
    Creating table auth_tests_extensionuser
    Creating table auth_tests_custompermissionsuser
    Creating table auth_tests_customusernonuniqueusername
    Creating table auth_tests_isactivetestuser1
    Creating table auth_tests_minimaluser
    Creating table auth_tests_nopassworduser
    Creating table auth_tests_concrete
    Creating table auth_tests_uuiduser
    Creating table auth_tests_email
    Creating table auth_tests_customuserwithfk
    Creating table auth_tests_integerusernameuser
    Creating table auth_tests_userwithdisabledlastloginfield
    Running deferred SQL...
Running migrations:
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying sites.0001_initial... OK
  Applying sites.0002_alter_domain_unique... OK
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
System check identified no issues (0 silenced).
test_help_text (auth_tests.test_validators.NumericPasswordValidatorTest) ... ok
test_validate (auth_tests.test_validators.NumericPasswordValidatorTest) ... ok
test_help_text (auth_tests.test_validators.MinimumLengthValidatorTest) ... ok
test_validate (auth_tests.test_validators.MinimumLengthValidatorTest) ... ok
test_ascii_validator (auth_tests.test_validators.UsernameValidatorsTests) ... test_unicode_validator (auth_tests.test_validators.UsernameValidatorsTests) ... test_help_text (auth_tests.test_validators.UserAttributeSimilarityValidatorTest) ... ok
test_validate (auth_tests.test_validators.UserAttributeSimilarityValidatorTest) ... ok
test_validate_property (auth_tests.test_validators.UserAttributeSimilarityValidatorTest) ... ok
test_empty_password_validator_help_text_html (auth_tests.test_validators.PasswordValidationTest) ... ok
test_get_default_password_validators (auth_tests.test_validators.PasswordValidationTest) ... ok
test_get_password_validators_custom (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_changed (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_changed_with_custom_validator (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_validators_help_text_html (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_validators_help_text_html_escaping (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_validators_help_texts (auth_tests.test_validators.PasswordValidationTest) ... ok
test_validate_password (auth_tests.test_validators.PasswordValidationTest) ... ok
test_help_text (auth_tests.test_validators.CommonPasswordValidatorTest) ... ok
test_validate (auth_tests.test_validators.CommonPasswordValidatorTest) ... ok
test_validate_custom_list (auth_tests.test_validators.CommonPasswordValidatorTest) ... ok
test_validate_django_supplied_file (auth_tests.test_validators.CommonPasswordValidatorTest) ... ok

======================================================================
FAIL: test_ascii_validator (auth_tests.test_validators.UsernameValidatorsTests) [<object object at 0x7f09ce330b50>] (invalid='trailingnewline\n')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/opendevin/.cache/miniconda3/envs/django__django__3.0/lib/python3.6/unittest/case.py", line 59, in testPartExecutor
    yield
  File "/home/opendevin/.cache/miniconda3/envs/django__django__3.0/lib/python3.6/unittest/case.py", line 523, in subTest
    yield
  File "/workspace/django__django__3.0/tests/auth_tests/test_validators.py", line 261, in test_ascii_validator
    v(invalid)
  File "/home/opendevin/.cache/miniconda3/envs/django__django__3.0/lib/python3.6/unittest/case.py", line 203, in __exit__
    self._raiseFailure("{} not raised".format(exc_name))
  File "/home/opendevin/.cache/miniconda3/envs/django__django__3.0/lib/python3.6/unittest/case.py", line 135, in _raiseFailure
    raise self.test_case.failureException(msg)
AssertionError: ValidationError not raised

======================================================================
FAIL: test_unicode_validator (auth_tests.test_validators.UsernameValidatorsTests) [<object object at 0x7f09ce330b50>] (invalid='trailingnewline\n')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/opendevin/.cache/miniconda3/envs/django__django__3.0/lib/python3.6/unittest/case.py", line 59, in testPartExecutor
    yield
  File "/home/opendevin/.cache/miniconda3/envs/django__django__3.0/lib/python3.6/unittest/case.py", line 523, in subTest
    yield
  File "/workspace/django__django__3.0/tests/auth_tests/test_validators.py", line 249, in test_unicode_validator
    v(invalid)
  File "/home/opendevin/.cache/miniconda3/envs/django__django__3.0/lib/python3.6/unittest/case.py", line 203, in __exit__
    self._raiseFailure("{} not raised".format(exc_name))
  File "/home/opendevin/.cache/miniconda3/envs/django__django__3.0/lib/python3.6/unittest/case.py", line 135, in _raiseFailure
    raise self.test_case.failureException(msg)
AssertionError: ValidationError not raised

----------------------------------------------------------------------
Ran 22 tests in 0.172s

FAILED (failures=2)
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
20:57:49 - opendevin:INFO: swe_env_box.py:218 - background logs:

>>> git apply ../gold.patch

20:57:55 - opendevin:INFO: swe_env_box.py:214 - exit code: 0
20:57:55 - opendevin:INFO: swe_env_box.py:215 -
20:57:55 - opendevin:INFO: swe_env_box.py:218 - background logs: dot

>>> ./tests/runtests.py --verbosity 2 auth_tests.test_validators

20:57:57 - opendevin:INFO: swe_env_box.py:214 - exit code: 0
20:57:57 - opendevin:INFO: swe_env_box.py:215 - Testing against Django installed in '/workspace/django__django__3.0/django' with up to 64 processes
Importing application auth_tests
Skipping setup of unused database(s): other.
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Operations to perform:
  Synchronize unmigrated apps: auth, auth_tests, contenttypes, messages, sessions, staticfiles
  Apply all migrations: admin, sites
Synchronizing apps without migrations:
  Creating tables...
    Creating table django_content_type
    Creating table auth_permission
    Creating table auth_group
    Creating table auth_user
    Creating table django_session
    Creating table auth_tests_customuser
    Creating table auth_tests_customuserwithoutisactivefield
    Creating table auth_tests_extensionuser
    Creating table auth_tests_custompermissionsuser
    Creating table auth_tests_customusernonuniqueusername
    Creating table auth_tests_isactivetestuser1
    Creating table auth_tests_minimaluser
    Creating table auth_tests_nopassworduser
    Creating table auth_tests_concrete
    Creating table auth_tests_uuiduser
    Creating table auth_tests_email
    Creating table auth_tests_customuserwithfk
    Creating table auth_tests_integerusernameuser
    Creating table auth_tests_userwithdisabledlastloginfield
    Running deferred SQL...
Running migrations:
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying sites.0001_initial... OK
  Applying sites.0002_alter_domain_unique... OK
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Cloning test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
System check identified no issues (0 silenced).
test_help_text (auth_tests.test_validators.NumericPasswordValidatorTest) ... ok
test_validate (auth_tests.test_validators.NumericPasswordValidatorTest) ... ok
test_help_text (auth_tests.test_validators.MinimumLengthValidatorTest) ... ok
test_validate (auth_tests.test_validators.MinimumLengthValidatorTest) ... ok
test_ascii_validator (auth_tests.test_validators.UsernameValidatorsTests) ... ok
test_unicode_validator (auth_tests.test_validators.UsernameValidatorsTests) ... ok
test_help_text (auth_tests.test_validators.UserAttributeSimilarityValidatorTest) ... ok
test_validate (auth_tests.test_validators.UserAttributeSimilarityValidatorTest) ... ok
test_validate_property (auth_tests.test_validators.UserAttributeSimilarityValidatorTest) ... ok
test_empty_password_validator_help_text_html (auth_tests.test_validators.PasswordValidationTest) ... ok
test_get_default_password_validators (auth_tests.test_validators.PasswordValidationTest) ... ok
test_get_password_validators_custom (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_changed (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_changed_with_custom_validator (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_validators_help_text_html (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_validators_help_text_html_escaping (auth_tests.test_validators.PasswordValidationTest) ... ok
test_password_validators_help_texts (auth_tests.test_validators.PasswordValidationTest) ... ok
test_validate_password (auth_tests.test_validators.PasswordValidationTest) ... ok
test_help_text (auth_tests.test_validators.CommonPasswordValidatorTest) ... ok
test_validate (auth_tests.test_validators.CommonPasswordValidatorTest) ... ok
test_validate_custom_list (auth_tests.test_validators.CommonPasswordValidatorTest) ... ok
test_validate_django_supplied_file (auth_tests.test_validators.CommonPasswordValidatorTest) ... ok

----------------------------------------------------------------------
Ran 22 tests in 0.169s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
20:57:57 - opendevin:INFO: swe_env_box.py:218 - background logs:
```
