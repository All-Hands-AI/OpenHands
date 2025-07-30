# Proposal for changing static type checking


## Use Cases for static checking

I feel like we actually have two use cases here:
* check the whole codebase(usually called from CI)
* check just the files about to commit.

I suggest we cleanly separate those two use cases and give them separate names.


### Check All

**Purpose:** Static check the whole repo

**main-entry-point:** `make check-all`

**Triggers:** CI(github), developer runs `make`

**Runtime:** long. Can take minutes.

**files-included:** all-files

**checks-included:** all-checks

**Setup:** Done by caller.


This should be the main check. As in, it should check the whole code of the project. So it serves as the source of truth, compared to the smaller "Check pre-commit".


### Check pre-commit

**Purpose:** Quickly check the files that are about to be committed, to avoid commits with small mistakes in them.

**main-entry-point:** `make check-pre-commit`

**Triggers:** `git commit`. It should not matter it called by a developer from the terminal, vsCode, or by the openhands-runtime.

**Runtime:** short. Long checks would interfere with development. My feeling is we should stay <30s on any reasonable machine.

**files-included:** just the files being staged.

**checks-included:** Only those that can be run in a reasonable time. Also, we might want to detect which modules(frontend, python-backend, vsCode-plugin) have any changes in them at all and only run the relevant checks.

**Setup:** The commit-hook must be set up so it can trigger
- Local Development: `make install-pre-commit-hooks` must be called by developer
- Openhands: Calls [.openhands/setup.sh](.openhands/setup.sh) during startup.


This check should defer to the main "check all files". Meaning that "check all" should serve as a single-source-of-truth, while this mechanism is mainly for convenience.
When "check pre-commit" and "check all" do something different, "check all" should be considered the "correct" behaviour.


## Environments


- Developer
  - terminal
    - `git commit`
    - `make check-all`
  - vsCode: `git commit`
- CI: `make check-all` called from [.github/workflows/lint.yml](.github/workflows/lint.yml)
- Openhands: `git commit`
