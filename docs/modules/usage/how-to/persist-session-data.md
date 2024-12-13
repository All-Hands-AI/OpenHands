# Persisting Session Data

Using the standard installation, the session data is stored in memory. Currently, if OpenHands' service is restarted,
previous sessions become invalid (a new secret is generated) and thus not recoverable.

## How to Persist Session Data

### Development Workflow
In the `config.toml` file, specify the following:
```
[core]
...
file_store="local"
file_store_path="/absolute/path/to/openhands/cache/directory"
jwt_secret="secretpass"
```
