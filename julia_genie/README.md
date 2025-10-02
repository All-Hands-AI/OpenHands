# PrayerHands Genie Server

This directory contains an experimental [Genie.jl](https://genieframework.com) server that mirrors the
Python FastAPI server's health endpoints while relying on
[PythonCall.jl](https://cjdoris.github.io/PythonCall.jl/stable/) to access existing Python
infrastructure in the PrayerHands codebase.

## Project goals

- Provide a high performance Julia-based entry point that can evolve towards parity with the
  Python FastAPI implementation.
- Demonstrate how PythonCall.jl can be used to reuse Python services without duplicating logic.
- Offer a foundation for progressively porting critical request paths to Julia/Genie.

## Layout

```
julia_genie/
├── Project.toml        # Julia project manifest for the Genie application
├── README.md           # This guide
├── src/PrayerHandsGenie.jl  # Genie module wrapping Python functionality
└── start.jl            # Helper script that instantiates dependencies and boots the server
```

The Julia module defines three routes (`/alive`, `/health`, and `/server_info`) that call into the
existing Python `openhands.runtime.utils.system_stats` module. The `server_info` endpoint therefore
returns exactly the same payload as the Python FastAPI version but is served from Genie.

## Prerequisites

1. Julia 1.10 or newer installed locally.
2. A working Python environment for PrayerHands (the same one used to run the FastAPI server).

The Julia server automatically adds the PrayerHands repository root to Python's `sys.path`, so you
should execute Julia from the repository root to ensure Python modules can be located.

## Running the server

From the root of the repository:

```bash
julia --project=julia_genie julia_genie/start.jl
```

The script activates the local Julia environment, installs dependencies on the first run, and
exposes the Genie server on `http://0.0.0.0:8001` by default.

You can override the host and port programmatically:

```julia
julia --project=julia_genie -e 'using PrayerHandsGenie; PrayerHandsGenie.start(host="127.0.0.1", port=8888)'
```

Once running, the Julia and Python servers can co-exist. This makes it easy to compare responses and
performance characteristics while gradually porting more features to Julia.

## Extending the server

- Add new Genie routes inside `setup_routes()` in `src/PrayerHandsGenie.jl`.
- Use `PythonCall.pyimport` to reuse business logic from the Python codebase until a native Julia
  implementation is available.
- For larger features, consider splitting Julia logic into additional modules under `src/` and
  adding complementary integration tests written in Julia.

## Troubleshooting

- **Python module import errors** – verify you're running Julia from the repository root and that
  the Python environment can import `openhands`. The server raises a descriptive error when Python
  dependencies are missing.
- **Port already in use** – pass a different `port` argument to `PrayerHandsGenie.start`.

This setup is intentionally lightweight so that future contributions can iterate rapidly on a Julia
Genie alternative to the existing FastAPI service.
