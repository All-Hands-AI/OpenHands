# Contributing

Thanks for your interest in contributing to OpenDevin! We welcome and appreciate contributions.

## How Can I Contribute?

There are many ways that you can contribute:

1. **Download and use** OpenDevin, and send [issues](https://github.com/OpenDevin/OpenDevin/issues) when you encounter something that isn't working or a feature that you'd like to see.
2. **Send feedback** after each session by [clicking the thumbs-up thumbs-down buttons](https://docs.all-hands.dev/modules/usage/feedback), so we can see where things are working and failing, and also build an open dataset for training code agents.
3. **Improve the Codebase** by sending PRs (see details below). In particular, we have some [good first issue](https://github.com/OpenDevin/OpenDevin/labels/good%20first%20issue) issues that may be ones to start on.

## Understanding OpenDevin's CodeBase

To understand the codebase, please refer to the README in each module:
- [frontend](./frontend/README.md)
- [agenthub](./agenthub/README.md)
- [evaluation](./evaluation/README.md)
- [opendevin](./opendevin/README.md)
    - [server](./opendevin/server/README.md)

When you write code, it is also good to write tests. Please navigate to the `tests` folder to see existing test suites.
At the moment, we have two kinds of tests: `unit` and `integration`. Please refer to the README for each test suite. These tests also run on GitHub's continuous integration to ensure quality of the project.

## Sending Pull Requests to OpenDevin

### 1. Fork the Official Repository
Fork the [OpenDevin repository](https://github.com/OpenDevin/OpenDevin) into your own account.
Clone your own forked repository into your local environment:

```shell
git clone git@github.com:<YOUR-USERNAME>/OpenDevin.git
```

### 2. Configure Git

Set the official repository as your [upstream](https://www.atlassian.com/git/tutorials/git-forks-and-upstreams) to synchronize with the latest update in the official repository.
Add the original repository as upstream:

```shell
cd OpenDevin
git remote add upstream git@github.com:OpenDevin/OpenDevin.git
```

Verify that the remote is set:

```shell
git remote -v
```

You should see both `origin` and `upstream` in the output.

### 3. Synchronize with Official Repository
Synchronize latest commit with official repository before coding:

```shell
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### 4. Set up the Development Environment

We have a separate doc [Development.md](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) that tells you how to set up a development workflow.

### 5. Write Code and Commit It

Once you have done this, you can write code, test it, and commit it to a branch (replace `my_branch` with an appropriate name):

```shell
git checkout -b my_branch
git add .
git commit
git push origin my_branch
```

### 6. Open a Pull Request

* On GitHub, go to the page of your forked repository, and create a Pull Request:
   - Click on `Branches`
   - Click on the `...` beside your branch and click on `New pull request`
   - Set `base repository` to `OpenDevin/OpenDevin`
   - Set `base` to `main`
   - Click `Create pull request`

The PR should appear in [OpenDevin PRs](https://github.com/OpenDevin/OpenDevin/pulls).

Then the OpenDevin team will review your code.

## PR Rules

### 1. Pull Request title
As described [here](https://github.com/commitizen/conventional-commit-types/blob/master/index.json), a valid PR title should begin with one of the following prefixes:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white space, formatting, missing semicolons, etc.)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)
- `ci`: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

For example, a PR title could be:
- `refactor: modify package path`
- `feat(frontend): xxxx`, where `(frontend)` means that this PR mainly focuses on the frontend component.

You may also check out previous PRs in the [PR list](https://github.com/OpenDevin/OpenDevin/pulls).

### 2. Pull Request description
- If your PR is small (such as a typo fix), you can go brief.
- If it contains a lot of changes, it's better to write more details.
