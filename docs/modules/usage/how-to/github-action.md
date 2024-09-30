# Using the OpenHands GitHub Action

This guide explains how to use the OpenHands GitHub Action, both within the OpenHands repository and in your own projects.

## Using the Action in the OpenHands Repository

To use the OpenHands GitHub Action in the OpenHands repository:

1. Create an issue in the repository.
2. Add the `fix-me` label to the issue.
3. The action will automatically trigger and attempt to resolve the issue.

## Installing the Action in a New Repository

To install the OpenHands GitHub Action in your own repository:

1. Create a `.github/workflows` directory in your repository if it doesn't already exist.
2. Create a new file named `openhands-resolver.yml` in the `.github/workflows` directory.
3. Copy the following content into the `openhands-resolver.yml` file:

```yaml
name: OpenHands Resolver

on:
  issues:
    types: [labeled]

jobs:
  resolve_issue:
    if: github.event.label.name == 'fix-me'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install git+https://github.com/All-Hands-AI/OpenHands.git
      - name: Run OpenHands
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          openhands resolve-issue --repo ${{ github.repository }} --issue ${{ github.event.issue.number }}

```

4. Commit and push the new file to your repository.

Now, whenever an issue in your repository is labeled with `fix-me`, the OpenHands GitHub Action will automatically trigger and attempt to resolve the issue.

Note: Make sure you have the necessary permissions and secrets set up in your repository for the action to work correctly.
