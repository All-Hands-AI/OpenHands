## Introduction

This folder contains unit tests that could be run locally.

Run all test:

```bash
uv run pytest ./tests/unit
```

Run specific test file:

```bash
uv run pytest ./tests/unit/test_llm_fncall_converter.py
```

Run specific unit test

```bash
uv run pytest ./tests/unit/test_llm_fncall_converter.py::test_convert_tool_call_to_string
```

For a more verbose output, to above calls the `-v` flag can be used (even more verbose: `-vv` and `-vvv`):

```bash
uv run pytest -v ./tests/unit/test_llm_fncall_converter.py
```

More details see [pytest doc](https://docs.pytest.org/en/latest/contents.html)
