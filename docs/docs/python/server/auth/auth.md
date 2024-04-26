---
sidebar_label: auth
title: server.auth.auth
---

#### get\_sid\_from\_token

```python
def get_sid_from_token(token: str) -> str
```

Retrieves the session id from a JWT token.

**Arguments**:

- `token` _str_ - The JWT token from which the session id is to be extracted.
  

**Returns**:

- `str` - The session id if found and valid, otherwise an empty string.

#### sign\_token

```python
def sign_token(payload: Dict[str, object]) -> str
```

Signs a JWT token.

