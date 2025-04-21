# OpenHands Fork Maintenance Guide

This guide outlines a strategy for maintaining a fork of the main OpenHands repository while incorporating custom patches and ensuring stability and security.

## Key Goals

1.  **Consistent Container Images:** Use a specific, matched pair of `runtime` and `agent` images across all environments.
2.  **Security & Intentional Updates:** Avoid automatic updates from upstream; intentionally review and integrate changes.
3.  **Local Patch Management:** Easily add, manage, and remove custom features or external PRs.

## 1. Initial Setup

First, ensure your fork is cloned locally and the original OpenHands repository is added as a remote named `upstream`.

```bash
# Clone your fork (replace with your fork URL)
# git clone <your-fork-url>
# cd OpenHands

# Add the main OpenHands repository as the 'upstream' remote
git remote add upstream https://github.com/All-Hands-AI/OpenHands.git

# Fetch upstream branches and tags
git fetch upstream
```

## 2. Container Image Management

To ensure consistency, build, tag, and distribute your own `runtime` and `agent` images based on your primary integration branch.

**a. Building Images:**

*   **Source Branch:** Images should be built by CI/CD processes triggered by commits to the `release/stable-with-patches` branch.
*   **Build Process:** Use the standard OpenHands build process (`docker build`, `make`, etc.).
*   **Base Image Consideration:** While the image is built *from* the code in `release/stable-with-patches`, consider how the underlying base OS/dependency image specified in the Dockerfile is kept up-to-date. This might involve periodically updating the base image tag in the Dockerfile itself as part of the fork maintenance.

*(Example - Adapt based on actual build commands, assuming build context is repo root)*
```bash
# Example: Build triggered by CI on release/stable-with-patches
git checkout release/stable-with-patches
MAIN_COMMIT_BASE=$(git log -n 1 --pretty=%H main) # Get the latest main commit integrated
BUILD_TAG="stable-$(date +%Y%m%d)-$(git rev-parse --short HEAD)-main-${MAIN_COMMIT_BASE:0:7}"

docker build -t your-registry/openhands-runtime:${BUILD_TAG} -f path/to/runtime/Dockerfile .
docker build -t your-registry/openhands-agent:${BUILD_TAG} -f path/to/agent/Dockerfile .

# Optionally, also tag as 'latest-stable' or similar
docker tag your-registry/openhands-runtime:${BUILD_TAG} your-registry/openhands-runtime:latest-stable
docker tag your-registry/openhands-agent:${BUILD_TAG} your-registry/openhands-agent:latest-stable
```

**b. Tagging Strategy:**

*   **Primary Tag:** Use a descriptive tag that indicates the source branch, date, commit SHA of the release branch, and potentially the `main` branch commit it's based on (see example above). E.g., `stable-YYYYMMDD-<release-sha>-main-<main-sha>`.
*   **Floating Tag (Optional):** Maintain a floating tag like `latest-stable` that points to the most recent successful build from `release/stable-with-patches`. This simplifies configuration for environments that should always use the latest stable version.

**c. Distribution:**

Push the tagged images (both specific and floating, if used) to your container registry (e.g., Docker Hub, GHCR, private registry).

```bash
# Example: Push images (adapt tags)
docker push your-registry/openhands-runtime:${BUILD_TAG}
docker push your-registry/openhands-agent:${BUILD_TAG}
docker push your-registry/openhands-runtime:latest-stable
docker push your-registry/openhands-agent:latest-stable
```

**d. Configuration:**

Update your OpenHands configurations (environment variables, config files, deployment manifests) to use your custom image tags. Prefer using a specific build tag for production/critical environments and the floating tag (`latest-stable`) for development or less critical deployments.

*   `RUNTIME_IMAGE=your-registry/openhands-runtime:latest-stable` (or specific tag)
*   `AGENT_IMAGE=your-registry/openhands-agent:latest-stable` (or specific tag)

Ensure these configurations are applied consistently across all environments (local dev, CI/CD, resolver flows).

**The CI/CD pipeline for `release/stable-with-patches` handles the build, tag, and push process automatically.** Configuration updates might be manual or automated depending on your deployment strategy.

## 3. Upstream Synchronization and Integration

This section describes how to keep your `main` branch in sync with `upstream/main` and how to integrate those updates into your `release/stable-with-patches` branch.

**a. Fetch Upstream Changes:**

Regularly fetch the latest changes from the `upstream` remote.

```bash
git fetch upstream
```

**b. Review Upstream Changes:**

Before integrating, review the changes made upstream since your `main` branch was last updated.

```bash
# Ensure you are on your local main branch
git checkout main

# See commit history difference
git log HEAD..upstream/main --oneline --graph

# See file changes
git diff HEAD..upstream/main
```
Pay close attention to changes in core components, interfaces between `agent` and `runtime`, dependencies, and security-related areas.

**c. Update Local `main` Branch (Rebase Recommended):**

Rebase your local `main` branch onto `upstream/main` to maintain a clean, linear history mirroring the upstream repository.

```bash
git checkout main
git rebase upstream/main
```

**Conflict Resolution (Main):** Conflicts here should be rare if you are not making direct commits to `main`. If they occur, resolve them, `git add <file>`, and `git rebase --continue`.

**Push Updated `main`:** Push the updated `main` branch to your fork's origin. Use `--force-with-lease` because you rebased.

```bash
git push origin main --force-with-lease
```

**d. Integrate Upstream Changes into `release/stable-with-patches` (Rebase):**

Regularly rebase your `release/stable-with-patches` branch onto the updated `main` branch. This incorporates the latest upstream changes while keeping your custom patches on top.

```bash
git checkout release/stable-with-patches
git rebase main
```

**Conflict Resolution (Release Branch):** Conflicts are more likely here, as upstream changes might clash with your custom patches. Carefully resolve conflicts, ensuring both upstream updates and your custom logic are correctly merged. Use `git status` to see conflicted files, edit them, then `git add <file>` and `git rebase --continue`. If you get stuck, `git rebase --abort` cancels the rebase.

**e. Testing:**

After rebasing `release/stable-with-patches`, thoroughly test your fork. Run linters, unit tests, integration tests, and perform manual checks focusing on areas affected by both upstream changes and your custom patches.

```bash
# Example: Run pre-commit checks and tests (adapt as needed)
make install-pre-commit-hooks
pre-commit run --all-files --config ./dev_config/python/.pre-commit-config.yaml
# cd frontend && npm run lint:fix && npm run build ; cd ..
# poetry run pytest ...
```

**f. Push Updated `release/stable-with-patches`:**

Push the rebased `release/stable-with-patches` branch to your fork's origin. Use `--force-with-lease` because you rebased.

```bash
git push origin release/stable-with-patches --force-with-lease
```

**This push will typically trigger your CI/CD pipeline to build and deploy new container images (as described in Section 2).**

## 4. Custom Development Workflow

All custom development and integration of external patches happen relative to the `release/stable-with-patches` branch.

**a. Create Feature Branches:**

For any new custom feature, bug fix, or integration of an external patch, create a dedicated branch based *off the latest `release/stable-with-patches`*.

```bash
# Ensure release/stable-with-patches is up-to-date locally
git checkout release/stable-with-patches
git pull origin release/stable-with-patches

# Create a branch for your feature/fix/patch
git checkout -b feature/my-new-widget
# Or for an external PR you want to test/integrate temporarily
git checkout -b feat/try-upstream-pr-456
```

**b. Develop and Commit:**

*   **Custom Features/Fixes:** Make your code changes on the feature branch. Commit frequently with clear messages.
*   **External Patches/PRs:** Apply the patch or cherry-pick commits from the external PR onto your feature branch.
    ```bash
    # Example: Cherry-pick commits for PR #456
    git fetch upstream pull/456/head:upstream-pr-456
    # Identify commits from the PR branch (e.g., using git log upstream-pr-456)
    git cherry-pick <commit-sha-1> <commit-sha-2> ...
    ```

**c. Keep Feature Branch Updated (Optional but Recommended):**

If `release/stable-with-patches` is updated (e.g., after a rebase onto `main`) while you are still working on your feature, rebase your feature branch onto the latest `release/stable-with-patches` to minimize future merge conflicts.

```bash
git checkout feature/my-new-widget
git pull origin release/stable-with-patches --rebase # Or git rebase origin/release/stable-with-patches
# Resolve conflicts if any
git push origin feature/my-new-widget --force-with-lease
```

**d. Create Pull Request (PR):**

Once your feature/fix is complete and tested locally, push the feature branch to your origin and create a Pull Request (PR) targeting the `release/stable-with-patches` branch.

```bash
git push origin feature/my-new-widget
# Go to your Git hosting platform (e.g., GitHub) and create a PR
# Base branch: release/stable-with-patches
# Compare branch: feature/my-new-widget
```

**e. Code Review and Merge:**

Follow your team's code review process. Once the PR is approved, merge it into `release/stable-with-patches` (typically using the merge button on the Git hosting platform, often configured to use squash or merge commits).

**f. Automatic Build and Deployment:**

The merge into `release/stable-with-patches` should automatically trigger the CI/CD pipeline (Section 2) to build, tag, and push new container images.

**g. Removing Patches:**

*   **External PR Merged Upstream:** If an external PR you integrated via a feature branch is merged into `upstream/main`, the changes will eventually be incorporated into `release/stable-with-patches` when it's rebased onto `main` (Section 3d). You can simply delete your temporary feature branch (`feature/try-upstream-pr-456`). The rebase of `release/stable-with-patches` might require conflict resolution if your temporary integration conflicts with the official merge.
*   **Custom Feature No Longer Needed:** If a custom feature merged into `release/stable-with-patches` needs to be reverted, use `git revert` on the `release/stable-with-patches` branch to undo the merge commit (or the specific commits if squashed). This creates a new commit that undoes the changes.

## 5. Workflow Summary

This revised workflow focuses on keeping `main` aligned with upstream and using `release/stable-with-patches` as the integration point for custom work and upstream updates.

**Regular Upkeep (e.g., daily/weekly):**

1.  **Sync `main` with Upstream:**
    *   `git checkout main`
    *   `git fetch upstream`
    *   Review `upstream/main` changes (`git log HEAD..upstream/main`)
    *   `git rebase upstream/main`
    *   `git push origin main --force-with-lease`

2.  **Update `release/stable-with-patches`:**
    *   `git checkout release/stable-with-patches`
    *   `git rebase main`
    *   **Resolve Conflicts:** Carefully merge upstream changes with your custom patches.
    *   **Test Thoroughly:** Run all checks and tests (`pre-commit`, `pytest`, etc.).
    *   `git push origin release/stable-with-patches --force-with-lease`
    *   *(CI/CD triggers image build/push from `release/stable-with-patches`)*

**Custom Feature Development:**

1.  **Start Feature:**
    *   `git checkout release/stable-with-patches`
    *   `git pull origin release/stable-with-patches`
    *   `git checkout -b feature/my-new-feature`
2.  **Develop & Commit:** Make changes, commit locally.
3.  **Update Feature Branch (Optional):** `git pull origin release/stable-with-patches --rebase`
4.  **Push & Create PR:**
    *   `git push origin feature/my-new-feature`
    *   Create PR on Git platform targeting `release/stable-with-patches`.
5.  **Review & Merge:** After approval, merge the PR into `release/stable-with-patches`.
    *   *(CI/CD triggers image build/push from `release/stable-with-patches`)*

**Deployment:**

*   Configure environments (dev, staging, prod) to use the desired container image tag (e.g., `your-registry/openhands-runtime:latest-stable` or a specific `stable-YYYYMMDD-...` tag) pushed by the CI/CD pipeline for `release/stable-with-patches`.

This workflow ensures `main` remains a clean mirror of upstream, while `release/stable-with-patches` continuously integrates both upstream updates and reviewed custom features, providing a stable base for builds and deployments.

