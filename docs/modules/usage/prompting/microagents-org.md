# Organization and User Microagents

## Purpose

Organizations and users can define microagents that apply to all repositories belonging to the organization or user.

## Usage

These microagents can be [any type of microagent](./microagents-overview#microagent-types) and will be loaded 
accordingly. However, they are applied to all repositories belonging to the organization or user.

Add a `.openhands` repository under the organization or user and create a `microagents` directory and place the
microagents in that directory.

## Example

General microagent file example for organization `Great-Co` located inside the `.openhands` repository:
`microagents/org-microagent.md`:
```
* Use type hints and error boundaries; validate inputs at system boundaries and fail with meaningful error messages.
* Document interfaces and public APIs; use implementation comments only for non-obvious logic.
* Follow the same naming convention for variables, classes, constants, etc. already used in each repository.
```
