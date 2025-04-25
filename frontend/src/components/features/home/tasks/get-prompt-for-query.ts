import { Provider } from "#/types/settings";
import { SuggestedTaskType } from "./task.types";

// Helper function to get provider-specific terminology
const getProviderTerms = (git_provider: Provider) => {
  if (git_provider === "gitlab") {
    return {
      requestType: "Merge Request",
      requestTypeShort: "MR",
      apiName: "GitLab API",
      tokenEnvVar: "GITLAB_TOKEN",
      ciSystem: "CI pipelines",
      ciProvider: "GitLab",
      requestVerb: "merge request",
    };
  }
  return {
    requestType: "Pull Request",
    requestTypeShort: "PR",
    apiName: "GitHub API",
    tokenEnvVar: "GITHUB_TOKEN",
    ciSystem: "GitHub Actions",
    ciProvider: "GitHub",
    requestVerb: "pull request",
  };
};

export const getMergeConflictPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => {
  const terms = getProviderTerms(git_provider);

  return `You are working on ${terms.requestType} #${issueNumber} in repository ${repo}. You need to fix the merge conflicts.
Use the ${terms.apiName} with the ${terms.tokenEnvVar} environment variable to retrieve the ${terms.requestTypeShort} details. Check out the branch from that ${terms.requestVerb} and look at the diff versus the base branch of the ${terms.requestTypeShort} to understand the ${terms.requestTypeShort}'s intention.
Then resolve the merge conflicts. If you aren't sure what the right solution is, look back through the commit history at the commits that introduced the conflict and resolve them accordingly.`;
};

export const getFailingChecksPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => {
  const terms = getProviderTerms(git_provider);

  return `You are working on ${terms.requestType} #${issueNumber} in repository ${repo}. You need to fix the failing CI checks.
Use the ${terms.apiName} with the ${terms.tokenEnvVar} environment variable to retrieve the ${terms.requestTypeShort} details. Check out the branch from that ${terms.requestVerb} and look at the diff versus the base branch of the ${terms.requestTypeShort} to understand the ${terms.requestTypeShort}'s intention.
Then use the ${terms.apiName} to look at the ${terms.ciSystem} that are failing on the most recent commit. Try and reproduce the failure locally.
Get things working locally, then push your changes. Sleep for 30 seconds at a time until the ${terms.ciProvider} ${terms.ciSystem.toLowerCase()} have run again. If they are still failing, repeat the process.`;
};

export const getUnresolvedCommentsPrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => {
  const terms = getProviderTerms(git_provider);

  return `You are working on ${terms.requestType} #${issueNumber} in repository ${repo}. You need to resolve the remaining comments from reviewers.
Use the ${terms.apiName} with the ${terms.tokenEnvVar} environment variable to retrieve the ${terms.requestTypeShort} details. Check out the branch from that ${terms.requestVerb} and look at the diff versus the base branch of the ${terms.requestTypeShort} to understand the ${terms.requestTypeShort}'s intention.
Then use the ${terms.apiName} to retrieve all the feedback on the ${terms.requestTypeShort} so far. If anything hasn't been addressed, address it and commit your changes back to the same branch.`;
};

export const getOpenIssuePrompt = (
  git_provider: Provider,
  issueNumber: number,
  repo: string,
) => {
  const terms = getProviderTerms(git_provider);

  return `You are working on Issue #${issueNumber} in repository ${repo}. Your goal is to fix the issue.
Use the ${terms.apiName} with the ${terms.tokenEnvVar} environment variable to retrieve the issue details and any comments on the issue. Then check out a new branch and investigate what changes will need to be made.
Finally, make the required changes and open up a ${terms.requestVerb}. Be sure to reference the issue in the ${terms.requestTypeShort} description.`;
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
