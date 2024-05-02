---
sidebar_label: logger
title: opendevin.core.logger
---

#### get\_console\_handler

```python
def get_console_handler()
```

Returns a console handler for logging.

#### get\_file\_handler

```python
def get_file_handler()
```

Returns a file handler for logging.

#### log\_uncaught\_exceptions

```python
def log_uncaught_exceptions(ex_cls, ex, tb)
```

Logs uncaught exceptions along with the traceback.

**Arguments**:

- `ex_cls` _type_ - The type of the exception.
- `ex` _Exception_ - The exception instance.
- `tb` _traceback_ - The traceback object.
  

**Returns**:

  None

## LlmFileHandler Objects

```python
class LlmFileHandler(logging.FileHandler)
```

__LLM prompt and response logging__


#### \_\_init\_\_

```python
def __init__(filename, mode='a', encoding='utf-8', delay=False)
```

Initializes an instance of LlmFileHandler.

**Arguments**:

- `filename` _str_ - The name of the log file.
- `mode` _str, optional_ - The file mode. Defaults to &#x27;a&#x27;.
- `encoding` _str, optional_ - The file encoding. Defaults to None.
- `delay` _bool, optional_ - Whether to delay file opening. Defaults to False.

#### emit

```python
def emit(record)
```

Emits a log record.

**Arguments**:

- `record` _logging.LogRecord_ - The log record to emit.

#### get\_llm\_prompt\_file\_handler

```python
def get_llm_prompt_file_handler()
```

Returns a file handler for LLM prompt logging.

#### get\_llm\_response\_file\_handler

```python
def get_llm_response_file_handler()
```

Returns a file handler for LLM response logging.

