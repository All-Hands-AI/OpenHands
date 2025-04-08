import { GitProvider } from "#/api/settings-service/settings-service.types";

export interface GitHubErrorReponse {
  message: string;
  documentation_url: string;
  status: number;
}

export interface GitUser {
  id: number;
  login: string;
  avatar_url: string;
  company: string | null;
  name: string | null;
  email: string | null;
}

export interface GitRepository {
  id: number;
  full_name: string;
  git_provider: GitProvider;
  stargazers_count?: number;
  link_header?: string;
}
