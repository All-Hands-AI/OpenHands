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
poetry run pytest ./tests/unit/test_micro_agents.py:test_coder_agent_with_summary
```

More details see [pytest doc](https://docs.pytest.org/en/latest/contents.html)