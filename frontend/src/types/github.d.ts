interface GitHubErrorReponse {
  message: string;
  documentation_url: string;
  status: number;
}

interface GitHubUser {
  id: number;
  login: string;
  avatar_url: string;
  company: string | null;
  name: string | null;
  email: string | null;
}

interface GitHubRepository {
  id: number;
  full_name: string;
  stargazers_count?: number;
  link_header?: string;
}

interface GitHubCommit {
  html_url: string;
  sha: string;
  commit: {
    author: {
      date: string; // ISO 8601
    };
  };
}

interface GithubAppInstallation {
  installations: { id: number }[];
}

// Extend Window interface to include GitHub Enterprise URL
declare global {
  interface Window {
    GITHUB_ENTERPRISE_URL?: string;
    GITHUB_API_URL?: string;
    GITHUB_WEB_URL?: string;
  }
}
