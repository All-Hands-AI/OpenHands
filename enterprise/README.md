# Closed Source extension of Openhands proper (OSS)

The closed source (CSS) code in the `/app` directory builds on top of open source (OSS) code, extending its functionality. The CSS code is entangled with the OSS code in two ways

- CSS stacks on top of OSS. For example, the middleware in CSS is stacked right on top of the middlewares in OSS. In `SAAS`, the middleware from BOTH repos will be present and running (which can sometimes cause conflicts)

- CSS overrides the implementation in OSS (only one is present at a time). For example, the server config [`SaasServerConfig`](https://github.com/All-Hands-AI/deploy/blob/main/app/server/config.py#L43) which overrides [`ServerConfig`](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/server/config/server_config.py#L8) on OSS. This is done through dynamic imports ([see here](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/server/config/server_config.py#L37-#L45))

Key areas that change on `SAAS` are

- Authentication
- User settings
- etc

## Authentication

| Aspect                    | OSS                                                    | CSS                                                                                                                                 |
| ------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Authentication Method** | User adds a personal access token (PAT) through the UI | User performs OAuth through the UI. The Github app provides a short-lived access token and refresh token                            |
| **Token Storage**         | PAT is stored in **Settings**                          | Token is stored in **GithubTokenManager** (a file store in our backend)                                                             |
| **Authenticated status**  | We simply check if token exists in `Settings`          | We issue a signed cookie with `github_user_id` during oauth, so subsequent requests with the cookie can be considered authenticated |

Note that in the future, authentication will happen via keycloak. All modifications for authentication will happen in CSS.

## GitHub Service

The github service is responsible for interacting with Github APIs. As a consequence, it uses the user's token and refreshes it if need be

| Aspect                    | OSS                                    | CSS                                            |
| ------------------------- | -------------------------------------- | ---------------------------------------------- |
| **Class used**            | `GitHubService`                        | `SaaSGitHubService`                            |
| **Token used**            | User's PAT fetched from `Settings`     | User's token fetched from `GitHubTokenManager` |
| **Refresh functionality** | **N/A**; user provides PAT for the app | Uses the `GitHubTokenManager` to refresh       |

NOTE: in the future we will simply replace the `GithubTokenManager` with keycloak. The `SaaSGithubService` should interact with keycloack instead.

# Areas that are BRITTLE!

## User ID vs User Token

- On OSS, the entire APP revolves around the Github token the user sets. `openhands/server` uses `request.state.github_token` for the entire app
- On CSS, the entire APP resolves around the Github User ID. This is because the cookie sets it, so `openhands/server` AND `deploy/app/server` depend on it and completly ignore `request.state.github_token` (token is fetched from `GithubTokenManager` instead)

Note that introducing Github User ID on OSS, for instance, will cause large breakages.
