# Contributing

Thanks for your interest in contributing to OpenDevin! We welcome and appreciate contributions.
To report bugs, create a [GitHub issue](https://github.com/OpenDevin/OpenDevin/issues/new/choose).

## Contribution Guide
### 1. Fork the Official Repository

Fork [OpenDevin repository](https://github.com/OpenDevin/OpenDevin) into your own account.
Clone your own forked repository into your local environment.

```shell
git clone git@github.com:<YOUR-USERNAME>/OpenDevin.git
```

### 2. Configure Git

Set the official repository as your [upstream](https://www.atlassian.com/git/tutorials/git-forks-and-upstreams) to synchronize with the latest update in the official repository.
Add the original repository as upstream

```shell
cd OpenDevin
git remote add upstream git@github.com:OpenDevin/OpenDevin.git
```

Verify that the remote is set.
```shell
git remote -v
```
You should see both `origin` and `upstream` in the output.

### 3. Synchronize with Official Repository
Synchronize latest commit with official repository before coding.

```shell
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### 4. Create a New Branch And Open a Pull Request
After you finish implementation, open forked repository. The source branch is your new branch, and the target branch is `OpenDevin/OpenDevin` `main` branch. Then PR should appears in [OpenDevin PRs](https://github.com/OpenDevin/OpenDevin/pulls).

Then OpenDevin team will review your code.

## PR Rules

### 1. Pull Request title

As described in [here](https://github.com/commitizen/conventional-commit-types/blob/master/index.json), a valid PR title should begin with one of the following prefixes:

- `feat`: A new feature
- `fix`: A bug fix
- `doc`: Documentation only changes
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `style`: A refactoring that improves code style
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `ci`: Changes to CI configuration files and scripts (example scopes: `.github`, `ci` (Buildkite))
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

For example, a PR title could be:
- `refactor: modify package path`
- `feat(frontend): xxxx`, where `(frontend)` means that this PR mainly focuses on the frontend component.

You may also check out previous PRs in the [PR list](https://github.com/OpenDevin/OpenDevin/pulls).

As described in [here](https://github.com/OpenDevin/OpenDevin/labels), we create several labels. Every PR should be tagged with the corresponding labels.

### 2. Pull Request description

- If your PR is small (such as a typo fix), you can go brief.
- If it is large and you have changed a lot, it's better to write more details.


## How to begin
Please refer to the README in each module:
- [frontend](./frontend/README.md)
- [agenthub](./agenthub/README.md)
- [evaluation](./evaluation/README.md)
- [opendevin](./opendevin/README.md)
    - [server](./opendevin/server/README.md)
    - [mock server](./opendevin/mock/README.md)

## Tests
Please navigate to `tests` folder to see existing test suites.
At the moment, we have two kinds of tests: `unit` and `integration`. Please refer to the README for each test suite. These tests also run on CI to ensure quality of
the project.
