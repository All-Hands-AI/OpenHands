# Integration tests

This directory implements integration tests that [was running in CI](https://github.com/All-Hands-AI/OpenHands/tree/23d3becf1d6f5d07e592f7345750c314a826b4e9/tests/integration).

[PR 3985](https://github.com/All-Hands-AI/OpenHands/pull/3985) introduce LLM-based editing, which requires access to LLM to perform edit. Hence, we remove integration tests from CI and intend to run them as nightly evaluation to ensure the quality of OpenHands softwares.

## To add new tests

Each test is a file named like `tXX_testname.py` where `XX` is a number.
Make sure to name the file for each test to start with `t` and ends with `.py`.

Each test should be structured as a subclass of [`BaseIntegrationTest`](./tests/base.py), where you need to implement `initialize_runtime` that setup the runtime enviornment before test, and `verify_result` that takes in a `Runtime` and history of `Event` and return a `TestResult`. See [t01_fix_simple_typo.py](./tests/t01_fix_simple_typo.py) and [t05_simple_browsing.py](./tests/t05_simple_browsing.py) for two representative examples.

```python
class TestResult(BaseModel):
    success: bool
    reason: str | None = None


class BaseIntegrationTest(ABC):
    """Base class for integration tests."""

    INSTRUCTION: str

    @classmethod
    @abstractmethod
    def initialize_runtime(cls, runtime: Runtime) -> None:
        """Initialize the runtime for the test to run."""
        pass

    @classmethod
    @abstractmethod
    def verify_result(cls, runtime: Runtime, histories: list[Event]) -> TestResult:
        """Verify the result of the test.

        This method will be called after the agent performs the task on the runtime.
        """
        pass
```


## Setup Environment and LLM Configuration

Please follow instruction [here](../README.md#setup) to setup your local
development environment and LLM.

## Start the evaluation

```bash
./evaluation/integration_tests/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [eval-num-workers] [eval_ids]
```

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for
    your LLM settings, as defined in your `config.toml`.
- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version
    you would like to evaluate. It could also be a release tag like `0.9.0`.
- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks,
    defaulting to `CodeActAgent`.
- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit`
    instances. By default, the script evaluates the entire Exercism test set
    (133 issues). Note: in order to use `eval_limit`, you must also set `agent`.
- `eval-num-workers`: the number of workers to use for evaluation. Default: `1`.
- `eval_ids`, e.g. `"1,3,10"`, limits the evaluation to instances with the
    given IDs (comma separated).

Example:
```bash
./evaluation/integration_tests/scripts/run_infer.sh llm.claude-35-sonnet-eval HEAD CodeActAgent
```
