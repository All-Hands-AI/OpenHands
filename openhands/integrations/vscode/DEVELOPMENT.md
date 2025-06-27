# VSCode Extension Development

This document provides instructions for developing and contributing to the OpenHands VSCode extension.

## Setup

To get started with development, you need to install the dependencies.

```bash
npm install
```

## Building the Extension

The VSCode extension is automatically built during the main OpenHands `pip install` process. However, you can also build it manually.

- **Package the extension:** This creates a `.vsix` file that can be installed in VSCode.
  ```bash
  npm run package-vsix
  ```

- **Compile TypeScript:** This compiles the source code without creating a package.
  ```bash
  npm run compile
  ```

## Code Quality and Testing

We use ESLint, Prettier, and TypeScript for code quality.

- **Run linting with auto-fixes:**
  ```bash
  npm run lint:fix
  ```

- **Run type checking:**
  ```bash
  npm run typecheck
  ```

- **Run tests:**
  ```bash
  npm run test
  ```

## Releasing a New Version

The extension has its own version number and is released independently of the main OpenHands application. The release process is automated via the `vscode-extension-build.yml` GitHub Actions workflow and is triggered by pushing a specially formatted Git tag.

### 1. Update the Version Number

Before creating a release, you must first bump the version number in the extension's `package.json` file.

1.  Open `openhands/integrations/vscode/package.json`.
2.  Find the `"version"` field and update it according to [Semantic Versioning](https://semver.org/) (e.g., from `"0.0.1"` to `"0.0.2"`).

### 2. Commit the Version Bump

Commit the change to `package.json` with a clear commit message.

```bash
git add openhands/integrations/vscode/package.json
git commit -m "chore(vscode): bump version to 0.0.2"
```

### 3. Create and Push the Tag

The release is triggered by a Git tag that **must** match the version in `package.json` and be prefixed with `ext-v`.

1.  **Create an annotated tag.** The tag name must be `ext-v` followed by the version number you just set.
    ```bash
    # Example for version 0.0.2
    git tag -a ext-v0.0.2 -m "Release VSCode extension v0.0.2"
    ```

2.  **Push the commit and the tag** to the `upstream` remote.
    ```bash
    # Push the branch with the version bump commit
    git push upstream <your-branch-name>

    # Push the specific tag
    git push upstream ext-v0.0.2
    ```

### 4. Finalize the Release on GitHub

Pushing the tag will automatically trigger the `VSCode Extension CI` workflow. This workflow will:
1.  Build the `.vsix` file.
2.  Create a new **draft release** on GitHub with the `.vsix` file attached as an asset.

To finalize the release:
1.  Go to the "Releases" page of the OpenHands repository on GitHub.
2.  Find the new draft release (e.g., `ext-v0.0.2`).
3.  Click "Edit" to write the release notes, describing the new features and bug fixes.
4.  Click the **"Publish release"** button.

The release is now public and available for users.
