# GitHub Release Workflow Plan

This document outlines the plan to automate the creation of GitHub releases for the VSCode extension, acknowledging that it is a sub-project within a larger monorepo.

## The Monorepo Challenge: Independent Extension Releases

The primary challenge is that the VSCode extension has its own versioning scheme (e.g., `0.0.1`) and release needs, which are separate from the main OpenHands project (e.g., `0.47.0`). A release of the extension should not be tied to a release of the main project. Our workflow must be able to distinguish between the two.

---

## Recommendation

We will proceed with using an **Independent Tag Prefix (`ext-v*`)**. It is the cleanest, most robust solution for managing a sub-project's releases within a monorepo.

---

## Phase 1: Planning and Design

- [x] **Decide on the release trigger:** On push of a new tag with the prefix `ext-v*`.
- [x] **Determine the versioning strategy:** The version will be read from the extension's `package.json` file. The Git tag (e.g., `ext-v0.0.2`) must match the version in `package.json`.
- [x] **Define the release notes strategy:** Manually write release notes for each release. The workflow will create a *draft* release, and a human will add notes and publish it.

## Phase 2: Implementation

- [x] **Choose a GitHub Action for creating releases:** Selected `ncipollo/release-action`.
- [x] **Update the `vscode-extension-build.yml` workflow:** Added a new `release` job triggered by `ext-v*` tags.
- [x] **Update action versions:** Ensured all GitHub Actions in the workflow are pinned to their latest stable versions.

## Phase 3: Testing and Troubleshooting

- [x] **Test the release workflow:** Pushed a test tag (`ext-v0.0.99-test`).
- [x] **Verification:** Confirmed that a draft release was created successfully with the `.vsix` artifact attached.
- [x] **Identify CI conflicts:** Discovered that the `ext-v*` tag also triggered the `ghcr-build.yml` workflow, causing CI failures.
- [x] **Resolve CI conflicts:** Modified `ghcr-build.yml` to ignore `ext-v*` tags, preventing unintended triggers.
- [ ] **Clean up test artifacts:** Delete the test tag (`ext-v0.0.99-test`) from the remote repository.

## Phase 4: Finalizing the Feature

- [ ] **Update the CLI installer:** Modify `openhands/cli/main.py` to attempt downloading the `.vsix` from the latest GitHub release before falling back to other methods.
- [ ] **Update documentation:** Document the new release process for other developers, explaining how to use the `ext-v*` tag to create a release.
