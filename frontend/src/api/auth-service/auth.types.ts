export interface AuthenticateResponse {
  message?: string;
  error?: string;
}

export interface GitHubAccessTokenResponse {
  access_token: string;
}
