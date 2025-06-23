# How to build custom E2B sandbox for OpenHands

[E2B](https://e2b.dev) is an [open-source](https://github.com/e2b-dev/e2b) secure cloud environment (sandbox) made for running AI-generated code and agents. E2B offers [Python](https://pypi.org/project/e2b/) and [JS/TS](https://www.npmjs.com/package/e2b) SDK to spawn and control these sandboxes.


1. Install the CLI with NPM.
    ```sh
    npm install -g @e2b/cli@latest
    ```
    Full CLI API is [here](https://e2b.dev/docs/cli/installation).

1. Build the sandbox
  ```sh
  e2b template build --dockerfile ./Dockerfile --name "openhands"
  ```
