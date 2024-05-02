## Introduction

This folder contains backend integration tests that rely on a mock LLM. It serves
two purposes:
1. Ensure the quality of development, including OpenDevin framework and agents.
2. Help contributors learn the workflow of OpenDevin, and examples of real interactions
with (powerful) LLM, without spending real money.

Why don't we launch an open-source model, e.g. LLAMA3? There are two reasons:
1. LLMs cannot guarantee determinism, meaning the test behavior might change.
2. CI machines are not powerful enough to run any LLM that is sophisticated enough
to finish the tasks defined in tests.

Note: integration tests are orthogonal to evaluations/benchmarks
as they serve different purposes. Although benchmarks could also
capture bugs, some of which may not be caught by tests, benchmarks
require real LLMs which are non-deterministic and costly.
We run integration test suite for every single commit, which is
not possible with benchmarks.

Known limitations:
1. To avoid the potential impact of non-determinism, we remove all special
characters and numbers (often used as PIDs) when doing the comparison. If two
prompts for the same task only differ in non-alpha characters, a wrong mock
response might be picked up.
2. It is required that the agent itself doesn't do anything non-deterministic,
including but not limited to using randomly generated numbers.

The folder is organised as follows:

```
├── README.md
├── conftest.py
├── mock
│   ├── [AgentName]
│   │   └── [TestName]
│   │       ├── prompt_*.log
│   │       ├── response_*.log
└── [TestFiles].py
```

where `conftest.py` defines the infrastructure needed to load real-world LLM prompts
and responses for mocking purpose. Prompts and responses generated during real runs
of agents with real LLMs are stored under `mock/AgentName/TestName` folders.

## Run Integration Tests

Take a look at `run-integration-tests.yml` to learn how integration tests are
launched in CI environment. Assuming you want to use `workspace` for testing, an
example is as follows:

```bash
rm -rf workspace; AGENT=PlannerAgent \
WORKSPACE_BASE="/Users/admin/OpenDevin/workspace" WORKSPACE_MOUNT_PATH="/Users/admin/OpenDevin/workspace" MAX_ITERATIONS=10 \
poetry run pytest -s ./tests/integration
```

Note: in order to run integration tests correctly, please ensure your workspace is empty.


## Write Integration Tests

To write an integration test, there are essentially two steps:

1. Decide your task prompt, and the result you want to verify.
2. Either construct LLM responses by yourself, or run OpenDevin with a real LLM. The system prompts and
LLM responses are recorded as logs, which you could then copy to test folder.
The following paragraphs describe how to do it.

Your `config.toml` should look like this:

```toml
LLM_MODEL="gpt-4-turbo"
LLM_API_KEY="<your-api-key>"
LLM_EMBEDDING_MODEL="openai"
WORKSPACE_MOUNT_PATH="<absolute-path-of-your-workspace>"
```

You can choose any model you'd like to generate the mock responses.
You can even handcraft mock responses, especially when you would like to test the behaviour of agent for corner cases. If you use a very weak model (e.g. 8B params), chance is most agents won't be able to finish the task.

```bash
# Remove logs if you are okay to lose logs. This helps us locate the prompts and responses quickly, but is NOT a must.
rm -rf logs
# Clear the workspace, otherwise OpenDevin might not be able to reproduce your prompts in CI environment. Feel free to change the workspace name and path. Be sure to set `WORKSPACE_MOUNT_PATH` to the same absolute path.
rm -rf workspace
mkdir workspace
# Depending on the complexity of the task you want to test, you can change the number of iterations limit. Change agent accordingly. If you are adding a new test, try generating mock responses for every agent.
poetry run python ./opendevin/core/main.py -i 10 -t "Write a shell script 'hello.sh' that prints 'hello'." -c "MonologueAgent" -d "./workspace"
```

**NOTE**: If your agent decide to support user-agent interaction via natural language (e.g., you will prompted to enter user resposes when running the above `main.py` command), you should create a file named `tests/integration/mock/<AgentName>/<TestName>/user_responses.log` containing all the responses in order you provided to the agent, delimited by newline ('\n'). This will be used to mock the STDIN during testing.

After running the above commands, you should be able to locate the real prompts
and responses logged. The log folder follows `logs/llm/%y-%m-%d_%H-%M.log` format.

Now, move all files under that folder to `tests/integration/mock/<AgentName>/<TestName>` folder. For example, moving all files from `logs/llm/24-04-23_21-55/` folder to
`tests/integration/mock/MonologueAgent/test_write_simple_script` folder.


That's it, you are good to go! When you launch an integration test, mock
responses are loaded and used to replace a real LLM, so that we get
deterministic and consistent behavior, and most importantly, without spending real
money.
