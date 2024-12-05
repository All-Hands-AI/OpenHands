import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { AxiosResponseHeaders, InternalAxiosRequestConfig } from "axios";
import { github } from "./github-axios-instance";
import { openHands } from "./open-hands-axios";
import { createAxiosError } from "./open-hands.utils";
import { GitHubAccessTokenResponse } from "./open-hands.types";
import { parse } from "path";

/**
 * Checks if the data is a GitHub error response
 * @param data The data to check
 * @returns Boolean indicating if the data is a GitHub error response
 */
export const isGitHubErrorReponse = <T extends object | Array<unknown>>(
  data: T | GitHubErrorReponse | null,
): data is GitHubErrorReponse =>
  !!data && "message" in data && data.message !== undefined;

/**
 * Converts to Axios error is the response is GithubErrorResponse
 */

const handleGithubResponse = (
  parsedData:
    | GitHubCommit[]
    | GitHubRepository[]
    | GitHubAppRepository
    | GitHubUser
    | GithubAppInstallation
    | GitHubAccessTokenResponse
    | GitHubErrorReponse,
  config: InternalAxiosRequestConfig,
  headers: AxiosResponseHeaders,
  status: number | undefined,
) => {
  if (isGitHubErrorReponse(parsedData)) {
    const error = createAxiosError(parsedData.message, config, status, headers);
    throw error;
  }

  return parsedData;
};

/**
 * Retrieves GitHub app installations for the user
 */
export const retrieveGitHubAppInstallations = async (): Promise<
  number[] | GitHubErrorReponse
> => {
  const response = await github.get<GithubAppInstallation>(
    "/user/installations",
    {
      params: {},
      transformResponse: function (
        this: InternalAxiosRequestConfig,
        data: string,
        headers,
        status,
      ) {
        const parsedData: GithubAppInstallation | GitHubErrorReponse =
          JSON.parse(data);
        return handleGithubResponse(parsedData, this, headers, status);
      },
    },
  );

  return response.data.installations.map(
    (installation: { id: number }) => installation.id,
  );
};

/**
 * Given a GitHub token, retrieves the repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
 */
export const retrieveGitHubAppRepositories = async (
  page = 1,
  per_page = 30,
  installation_index: number,
  installations: number[],
) => {
  const installation_id = installations[installation_index];
  const response = await openHands.get<GitHubAppRepository>(
    "/api/github/repositories",
    {
      params: {
        sort: "pushed",
        page,
        per_page,
        installation_id,
      },
      transformResponse: function (
        this: InternalAxiosRequestConfig,
        data: string,
        headers,
        status,
      ) {
        const parsedData: GitHubAppRepository | GitHubErrorReponse =
          JSON.parse(data);
        return handleGithubResponse(parsedData, this, headers, status);
      },
    },
  );

  const link = response.headers.link ?? "";
  const nextPage = extractNextPageFromLink(link);
  const nextInstallation = nextPage
    ? installation_index
    : !nextPage && installation_index + 1 < installations.length
      ? installation_index + 1
      : null;

  return {
    data: response.data.repositories,
    nextPage,
    installation_index: nextInstallation,
  };
};

/**
 * Given a GitHub token, retrieves the repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
 */
export const retrieveGitHubUserRepositories = async (
  page = 1,
  per_page = 30,
) => {
  const response = await openHands.get<GitHubRepository[]>(
    "/api/github/repositories",
    {
      params: {
        sort: "pushed",
        page,
        per_page,
      },
      transformResponse: function (
        this: InternalAxiosRequestConfig,
        data: string,
        headers,
        status,
      ) {
        const parsedData: GitHubRepository[] | GitHubErrorReponse =
          JSON.parse(data);

        return handleGithubResponse(parsedData, this, headers, status);
      },
    },
  );

  const link = response.headers.link ?? "";
  const nextPage = extractNextPageFromLink(link);

  return { data: response.data, nextPage };
};

/**
 * Given a GitHub token, retrieves the authenticated user
 * @param token The GitHub token
 * @returns The authenticated user or an error response
 */
export const retrieveGitHubUser = async () => {
  const response = await github.get<GitHubUser>("/user", {
    transformResponse: function (
      this: InternalAxiosRequestConfig,
      data: string,
      headers,
      status,
    ) {
      const parsedData: GitHubUser | GitHubErrorReponse = JSON.parse(data);
      return handleGithubResponse(parsedData, this, headers, status);
    },
  });

  const { data } = response;

  const user: GitHubUser = {
    id: data.id,
    login: data.login,
    avatar_url: data.avatar_url,
    company: data.company,
    name: data.name,
    email: data.email,
  };

  return user;
};

export const retrieveLatestGitHubCommit = async (
  repository: string,
): Promise<GitHubCommit> => {
  const response = await github.get<GitHubCommit[]>(
    `/repos/${repository}/commits`,
    {
      params: {
        per_page: 1,
      },
      transformResponse: function (
        this: InternalAxiosRequestConfig,
        data: string,
        headers,
        status,
      ) {
        const parsedData: GitHubCommit[] | GitHubErrorReponse =
          JSON.parse(data);

        return handleGithubResponse(parsedData, this, headers, status);
      },
    },
  );

  return response.data[0];
};
