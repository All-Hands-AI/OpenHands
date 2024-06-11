## Introduction

This folder contains unit tests that could be run locally.

Run all test:

```bash
poetry run pytest ./tests/unit
```

Run specific test file:

```bash
poetry run pytest ./tests/unit/test_micro_agents.py
```

Run specific unit test

```bash
poetry run pytest ./tests/unit/test_micro_agents.py::test_coder_agent_with_summary
```

For a more verbose output, to above calls the `-v` flag can be used (even more verbose: `-vv` and `-vvv`):

```bash
poetry run pytest -v ./tests/unit/test_micro_agents.py
```

More details see [pytest doc](https://docs.pytest.org/en/latest/contents.html)
