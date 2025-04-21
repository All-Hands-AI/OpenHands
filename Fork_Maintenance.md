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

To ensure consistency, build, tag, and distribute your own `runtime` and `agent` images.

**a. Building Images:**

Use the standard OpenHands build process, typically involving `docker build` or `make` targets defined in the repository. Identify the specific Dockerfiles or build commands for the `runtime` and `agent` images.

*(Example - Adapt based on actual build commands)*
```bash
# Example: Build the runtime image
docker build -t your-registry/openhands-runtime:<your-tag> -f path/to/runtime/Dockerfile .

# Example: Build the agent image
docker build -t your-registry/openhands-agent:<your-tag> -f path/to/agent/Dockerfile .
```

**b. Tagging Strategy:**

Use a consistent tagging scheme. Options include:
*   **Commit SHA:** `your-registry/openhands-runtime:$(git rev-parse --short HEAD)` - Precise, but requires updating configurations frequently.
*   **Version/Date Tag:** `your-registry/openhands-runtime:v1.2.3-custom` or `your-registry/openhands-runtime:20250421` - Easier to manage stable versions.
*   **Branch Name:** `your-registry/openhands-runtime:main-custom` - For development/testing branches.

**Choose a tag (e.g., `stable-custom`) that you will consistently use for your deployments.**

**c. Distribution:**

Push the tagged images to a container registry accessible by your resolver flow and local environments (e.g., Docker Hub, GitHub Container Registry, private registry).

```bash
# Example: Push images
docker push your-registry/openhands-runtime:<your-tag>
docker push your-registry/openhands-agent:<your-tag>
```

**d. Configuration:**

Update your OpenHands configuration (e.g., environment variables, config files) to explicitly use your custom image tags:

*   `RUNTIME_IMAGE=your-registry/openhands-runtime:<your-tag>`
*   `AGENT_IMAGE=your-registry/openhands-agent:<your-tag>`

Ensure these configurations are applied wherever OpenHands runs (local dev, CI/CD, resolver flows).

**When you update your fork and need new images, repeat steps a-c with a *new tag* and then update the configuration (d) to roll out the change.**

## 3. Upstream Synchronization and Security

Keep your fork updated with the main repository intentionally.

**a. Fetch Upstream Changes:**

Regularly fetch the latest changes from the `upstream` remote.

```bash
git fetch upstream
```

**b. Review Changes:**

Before merging, review the changes made upstream since your last sync.

```bash
# See commit history difference
git log HEAD..upstream/main --oneline --graph

# See file changes
git diff HEAD..upstream/main
```
Pay close attention to changes in core components, interfaces between `agent` and `runtime`, dependencies, and security-related areas.

**c. Integrate Changes (Rebase Recommended):**

It's generally recommended to **rebase** your main branch (or the branch you base your features on) onto the upstream main branch. This maintains a linear history.

```bash
# Ensure you are on your main branch (e.g., 'main' or 'master')
git checkout main

# Rebase your main branch onto the upstream main branch
git rebase upstream/main
```

**Conflict Resolution:** If conflicts occur during rebase, Git will pause. Edit the conflicted files to resolve the differences, then use `git add <file>` and `git rebase --continue`. If you get stuck, `git rebase --abort` will cancel the rebase.

**Alternative (Merge):** If rebasing proves too complex due to extensive changes or conflicts, you can use merge:
```bash
git checkout main
git merge upstream/main -m "Merge upstream/main into main"
```
This creates a merge commit, which can make history less linear but might be safer for complex integrations.

**d. Testing:**

After syncing (rebase or merge), thoroughly test your fork, especially areas affected by upstream changes and your custom patches. Run linters, unit tests, and integration tests if available.

```bash
# Example: Run pre-commit checks and tests (adapt as needed)
make install-pre-commit-hooks
pre-commit run --all-files --config ./dev_config/python/.pre-commit-config.yaml
# cd frontend && npm run lint:fix && npm run build ; cd ..
# poetry run pytest ...
```

**e. Update Container Images:**

If the upstream changes necessitate rebuilding your container images (e.g., dependency updates, core changes), rebuild, tag (potentially with a new tag), and push them (Section 2). Update your configurations accordingly.

**f. Push Changes:**

Push the updated main branch to your fork origin. Use `--force-with-lease` if you rebased.

```bash
# If you rebased:
git push origin main --force-with-lease

# If you merged:
git push origin main
```

## 4. Local Patch Management

Manage your custom features or temporary PR inclusions using feature branches.

**a. Create Feature Branches:**

For each distinct patch, custom feature, or external PR you want to include, create a dedicated branch off your main branch.

```bash
# Ensure main is up-to-date first (Section 3)
git checkout main
git pull origin main # Or ensure it matches the rebased/merged state

# Create a branch for your patch
git checkout -b feature/my-custom-patch
# Or for an external PR
git checkout -b feat/upstream-pr-123
```

**b. Apply Patches:**

*   **For your own features:** Develop directly on the feature branch. Commit your changes.
*   **For external PRs:** Fetch the PR branch into your local repo and cherry-pick the commits onto your feature branch.
    ```bash
    # Example: Fetch PR #123 from upstream
    git fetch upstream pull/123/head:upstream-pr-123
    git checkout feat/upstream-pr-123
    # Identify commits from the PR branch (e.g., using git log upstream-pr-123)
    git cherry-pick <commit-sha-1> <commit-sha-2> ...
    ```
*   **Using `.patch` files:**
    ```bash
    git apply path/to/patchfile.patch
    git commit -am "Apply patch for feature X"
    ```

**c. Keeping Patches Updated (Rebasing Feature Branches):**

After you update your `main` branch by syncing with `upstream` (Section 3), rebase your feature branches onto the updated `main`.

```bash
git checkout feature/my-custom-patch
git rebase main

# Resolve any conflicts, then: git add <file>, git rebase --continue
# Finally, push the rebased branch (forcefully)
git push origin feature/my-custom-patch --force-with-lease
```
Repeat for all active feature branches.

**d. Integrating Patches for Deployment:**

To create a build that includes specific patches, create an integration branch or directly build from a branch that merges the desired features:

```bash
# Option 1: Integration Branch
git checkout main
git checkout -b release/stable-with-patches
git merge feature/my-custom-patch --no-ff -m "Integrate custom patch"
git merge feat/upstream-pr-123 --no-ff -m "Integrate upstream PR #123"
# Build/test/tag images from this 'release/stable-with-patches' branch

# Option 2: Build directly from a feature branch if it's the only one needed
# Build/test/tag images from 'feature/my-custom-patch'
```

**e. Removing Obsolete Patches:**

*   **Upstream PR Merged:** If an external PR you included (`feat/upstream-pr-123`) gets merged into `upstream/main`, your next rebase of `main` onto `upstream/main` (Section 3c) will incorporate those changes officially.
    *   Delete your local feature branch for that PR: `git branch -D feat/upstream-pr-123`
    *   Delete the remote branch: `git push origin --delete feat/upstream-pr-123`
    *   If you used an integration branch (d), you'll need to recreate it without merging the now-obsolete feature branch.
*   **Custom Patch No Longer Needed:** Simply delete the feature branch locally and remotely. Recreate any integration branches without merging it.

## 5. Workflow Summary

1.  **Sync `main`:** `git checkout main`, `git fetch upstream`, `git rebase upstream/main` (review changes first!). Resolve conflicts. Test. `git push origin main --force-with-lease`.
2.  **Update Feature Branches:** For each `feature/xxx` branch: `git checkout feature/xxx`, `git rebase main`. Resolve conflicts. Test. `git push origin feature/xxx --force-with-lease`.
3.  **Build/Deploy:**
    *   Decide which patches are needed for the current build.
    *   Create/update an integration branch (e.g., `release/stable-custom`) by merging `main` and the required `feature/xxx` branches.
    *   Build `runtime` and `agent` images from this integration branch.
    *   Tag images with your chosen scheme (e.g., `stable-custom`, `YYYYMMDD`).
    *   Push images to your registry.
    *   Update OpenHands configurations to use the new image tags.
4.  **Clean Up:** Regularly delete feature branches for patches that have been merged upstream or are no longer needed.

This workflow balances staying up-to-date with upstream, maintaining your custom changes, and ensuring consistent, secure deployments.

