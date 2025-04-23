import { Provider } from "#/types/settings";
import { SuggestedTaskType } from "./task.types";

export const getMergeConflictPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => `You are working on Pull Request #${issueNumber} in repository ${repo}. You need to fix the merge conflicts.
Use the GitHub API to retrieve the PR details. Check out the branch from that pull request and look at the diff versus the base branch of the PR to understand the PR's intention.
Then resolve the merge conflicts. If you aren't sure what the right solution is, look back through the commit history at the commits that introduced the conflict and resolve them accordingly.`;

export const getFailingChecksPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => `You are working on Pull Request #${issueNumber} in repository ${repo}. You need to fix the failing CI checks.
Use the GitHub API to retrieve the PR details. Check out the branch from that pull request and look at the diff versus the base branch of the PR to understand the PR's intention.
Then use the GitHub API to look at the GitHub Actions that are failing on the most recent commit. Try and reproduce the failure locally.
Get things working locally, then push your changes. Sleep for 30 seconds at a time until the GitHub actions have run again. If they are still failing, repeat the process.`;

export const getUnresolvedCommentsPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => `You are working on Pull Request #${issueNumber} in repository ${repo}. You need to resolve the remaining comments from reviewers.
Use the GitHub API to retrieve the PR details. Check out the branch from that pull request and look at the diff versus the base branch of the PR to understand the PR's intention.
Then use the GitHub API to retrieve all the feedback on the PR so far. If anything hasn't been addressed, address it and commit your changes back to the same branch.`;

export const getOpenIssuePrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => `You are working on Issue #${issueNumber} in repository ${repo}. Your goal is to fix the issue
Use the GitHub API to retrieve the issue details and any comments on the issue. Then check out a new branch and investigate what changes will need to be made
Finally, make the required changes and open up a pull request. Be sure to reference the issue in the PR description`;

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
