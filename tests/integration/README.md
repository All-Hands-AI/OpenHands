# Introduction

This folder contains backend integration tests that rely on a mock LLM. It serves
two purposes:

1. Ensure the quality of development, including OpenHands framework and agents.
2. Help contributors learn the workflow of OpenHands, and examples of real interactions
with (powerful) LLM, without spending real money.

## Why don't we launch an open-source model, e.g. LLAMA3?

There are two reasons:

1. LLMs cannot guarantee determinism, meaning the test behavior might change.
2. CI machines are not powerful enough to run any LLM that is sophisticated enough
to finish the tasks defined in tests.

Note: integration tests are orthogonal to evaluations/benchmarks
as they serve different purposes. Although benchmarks could also
capture bugs, some of which may not be caught by tests, benchmarks
require real LLMs which are non-deterministic and costly.
We run integration test suite for every single commit, which is
not possible with benchmarks.

## Known limitations

1. To avoid the potential impact of non-determinism, we remove all special
characters when doing the comparison. If two prompts for the same task only
differ in non-alphanumeric characters, a wrong mock response might be picked up.
2. It is required that everything has to be deterministic. For example, agent
must not use randomly generated numbers.

The folder is organised as follows:

```
├── README.md
├── conftest.py
├── mock
    ├── [RuntimeType]
│   |   ├── [AgentName]
│   │       └── [TestName]
│   │           ├── prompt_*.log
│   │           ├── response_*.log
└── [TestFiles].py
```

where `conftest.py` defines the infrastructure needed to load real-world LLM prompts
and responses for mocking purpose. Prompts and responses generated during real runs
of agents with real LLMs are stored under `mock/AgentName/TestName` folders.


## Run Integration Tests

[ghcr_runtime.yml](../../.github/workflows/ghcr_runtime.yml) runs integration tests in a CI environment.

*Note:* If you are using docker desktop make sure that your version is up to date and "Enable Host Networking"
is checked (Under settings -> Resources -> Network ). Otherwise the integration tests may hang with the
message `Getting container logs...` repeated ad infinitum.

You can run:

```bash
# for event stream
TEST_RUNTIME=eventstream TEST_ONLY=true ./tests/integration/regenerate.sh
```

to run all integration tests until the first failure occurs.

If you'd only plan to run a specific test, set environment variable
`ONLY_TEST_NAME` to the actual test name. If you only want to run a specific agent,
set environment variable `ONLY_TEST_AGENT` to the agent. You could also use both,
e.g.

```bash
TEST_ONLY=true ONLY_TEST_NAME="test_simple_task_rejection" ONLY_TEST_AGENT="ManagerAgent" ./tests/integration/regenerate.sh
```

## Regenerate Integration Tests

When you make changes to an agent's prompt, the integration tests will fail. You'll need to regenerate them
by running the following command from OpenHands's project root directory:

```bash
TEST_RUNTIME=eventstream ./tests/integration/regenerate.sh
```

Please note that this will:

1. Run existing tests first. If a test passes, then no regeneration would happen.
2. Regenerate the prompts, but attempt to use existing responses from LLM (if any).
For example, if you only fix a typo in the prompt, it shouldn't affect LLM's behaviour.
If we rerun integration tests against a real LLM, then due to LLM's non-deterministic nature,
a series of different prompts and responses will be generated, causing a lot of
unnecessary diffs which are hard to review. If you want to skip this step, see below
sections.
3. Rerun the failed test again. If it succeeds, continue to the next test or agent.
If it fails again, goto next step.
4. Rerun integration tests against a real LLM, record all prompts and
responses, and replace the existing test artifacts (if any).
5. Rerun the failed test again. If it succeeds, continue to the next test or agent.
If it fails again, abort the script.

Note that step 4 calls *real* LLM_MODEL only for failed tests that cannot be fixed
by regenerating prompts alone, but it still costs money! If you don't want
to cover the cost, ask one of the maintainers to regenerate for you. Before asking,
please try running the script first *without* setting `LLM_API_KEY`.
Chance is, the test could be fixed after step 2.

## Regenerate Integration Tests without testing first

If you want to regenerate all prompts and/or responses without running the existing tests first, you can run:

```bash
FORCE_REGENERATE=true ./tests/integration/regenerate.sh
```

This will skip the first step and directly regenerate all tests when you know that the tests will fail due to changes in the prompt or the agent code itself and will save time.

## Regenerate a Specific Agent and/or Test

If you only want to run a specific test, set environment variable
`ONLY_TEST_NAME` to the test name. If you only want to run a specific agent,
set environment variable `ONLY_TEST_AGENT` to the agent. You could also use both,
e.g.

```bash
ONLY_TEST_NAME="test_write_simple_script" ONLY_TEST_AGENT="CodeActAgent" ./tests/integration/regenerate.sh
```

## Force Regenerate with real LLM

Sometimes, step 2 would fix the broken test by simply reusing existing responses
from LLM. This may not be what you want - for example, you might have greatly improved
the prompt that you believe the LLM will do a better job using fewer steps, or you might
have added a new action type and you think the LLM should be able to use the new type.
In this case you can skip step 2 and run integration tests against a real LLM.
Simply set `FORCE_USE_LLM` environmental variable to true, or run the script like this:

```bash
FORCE_USE_LLM=true ./tests/integration/regenerate.sh
```

Note: `FORCE_USE_LLM` doesn't take effect if all tests are passing. If you want to
regenerate regardless, you could remove everything under the
`tests/integration/mock/[agent]/[test_name]` folder.

## Known Issues

The test framework cannot handle non-determinism. If anything in the prompt (including
observed result after executing an action) is non-deterministic (e.g. a PID), the
test would fail. In this case, you might want to change conftest.py to filter out
numbers or any other known patterns when matching prompts for your test.

## Write a new Integration Test

To write an integration test, there are essentially two steps:

1. Decide your task prompt, and the result you want to verify.
2. Add your prompt to the `regenerate.sh` script.

**NOTE**: If your agent decides to support user-agent interaction via natural
language (e.g., you're prompted to enter user responses when running the above
`main.py` command), you should create a file named
`tests/integration/mock/<AgentName>/<TestName>/user_responses.log`
containing all the responses in order you provided to the agent,
delimited by a single newline ('\n'). This will be used to mock the STDIN during testing.

That's it, you are good to go! When you launch an integration test, mock
responses are loaded and used to replace a real LLM's response, so that we get
deterministic and consistent behavior, and most importantly, without spending real
money.
