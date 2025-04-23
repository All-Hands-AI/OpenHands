import { Provider } from "#/types/settings";
import { SuggestedTaskType } from "./task.types";

export const getMergeConflictPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => {
  if (git_provider === "gitlab") {
    return `You are working on Merge Request #${issueNumber} in repository ${repo}. You need to fix the merge conflicts.
Use the GitLab API with the GITLAB_TOKEN environment variable to retrieve the MR details. Check out the branch from that merge request and look at the diff versus the base branch of the MR to understand the MR's intention.
Then resolve the merge conflicts. If you aren't sure what the right solution is, look back through the commit history at the commits that introduced the conflict and resolve them accordingly.`;
  } else {
    return `You are working on Pull Request #${issueNumber} in repository ${repo}. You need to fix the merge conflicts.
Use the GitHub API with the GITHUB_TOKEN environment variable to retrieve the PR details. Check out the branch from that pull request and look at the diff versus the base branch of the PR to understand the PR's intention.
Then resolve the merge conflicts. If you aren't sure what the right solution is, look back through the commit history at the commits that introduced the conflict and resolve them accordingly.`;
  }
};

export const getFailingChecksPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => {
  if (git_provider === "gitlab") {
    return `You are working on Merge Request #${issueNumber} in repository ${repo}. You need to fix the failing CI checks.
Use the GitLab API with the GITLAB_TOKEN environment variable to retrieve the MR details. Check out the branch from that merge request and look at the diff versus the base branch of the MR to understand the MR's intention.
Then use the GitLab API to look at the CI pipelines that are failing on the most recent commit. Try and reproduce the failure locally.
Get things working locally, then push your changes. Sleep for 30 seconds at a time until the GitLab pipelines have run again. If they are still failing, repeat the process.`;
  } else {
    return `You are working on Pull Request #${issueNumber} in repository ${repo}. You need to fix the failing CI checks.
Use the GitHub API with the GITHUB_TOKEN environment variable to retrieve the PR details. Check out the branch from that pull request and look at the diff versus the base branch of the PR to understand the PR's intention.
Then use the GitHub API to look at the GitHub Actions that are failing on the most recent commit. Try and reproduce the failure locally.
Get things working locally, then push your changes. Sleep for 30 seconds at a time until the GitHub actions have run again. If they are still failing, repeat the process.`;
  }
};

export const getUnresolvedCommentsPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => {
  if (git_provider === "gitlab") {
    return `You are working on Merge Request #${issueNumber} in repository ${repo}. You need to resolve the remaining comments from reviewers.
Use the GitLab API with the GITLAB_TOKEN environment variable to retrieve the MR details. Check out the branch from that merge request and look at the diff versus the base branch of the MR to understand the MR's intention.
Then use the GitLab API to retrieve all the feedback on the MR so far. If anything hasn't been addressed, address it and commit your changes back to the same branch.`;
  } else {
    return `You are working on Pull Request #${issueNumber} in repository ${repo}. You need to resolve the remaining comments from reviewers.
Use the GitHub API with the GITHUB_TOKEN environment variable to retrieve the PR details. Check out the branch from that pull request and look at the diff versus the base branch of the PR to understand the PR's intention.
Then use the GitHub API to retrieve all the feedback on the PR so far. If anything hasn't been addressed, address it and commit your changes back to the same branch.`;
  }
};

export const getOpenIssuePrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => {
  if (git_provider === "gitlab") {
    return `You are working on Issue #${issueNumber} in repository ${repo}. Your goal is to fix the issue
Use the GitLab API with the GITLAB_TOKEN environment variable to retrieve the issue details and any comments on the issue. Then check out a new branch and investigate what changes will need to be made
Finally, make the required changes and open up a merge request. Be sure to reference the issue in the MR description`;
  } else {
    return `You are working on Issue #${issueNumber} in repository ${repo}. Your goal is to fix the issue
Use the GitHub API with the GITHUB_TOKEN environment variable to retrieve the issue details and any comments on the issue. Then check out a new branch and investigate what changes will need to be made
Finally, make the required changes and open up a pull request. Be sure to reference the issue in the PR description`;
  }
};

export const getPromptForQuery = (
  git_provider: Provider,
  type: SuggestedTaskType,
  issueNumber: number,
  repo: string,
) => {
  switch (type) {
    case "MERGE_CONFLICTS":
      return getMergeConflictPrompt(git_provider, issueNumber, repo);
    case "FAILING_CHECKS":
      return getFailingChecksPrompt(git_provider, issueNumber, repo);
    case "UNRESOLVED_COMMENTS":
      return getUnresolvedCommentsPrompt(git_provider, issueNumber, repo);
    case "OPEN_ISSUE":
      return getOpenIssuePrompt(git_provider, issueNumber, repo);
    default:
      return "";
  }
};
