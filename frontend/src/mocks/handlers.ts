import { delay, http, HttpResponse } from "msw";
import { GetConfigResponse } from "#/api/open-hands.types";
import { DEFAULT_SETTINGS } from "#/services/settings";

const userPreferences = {
  settings: {
    llm_model: DEFAULT_SETTINGS.LLM_MODEL,
    llm_base_url: DEFAULT_SETTINGS.LLM_BASE_URL,
    llm_api_key: DEFAULT_SETTINGS.LLM_API_KEY,
    agent: DEFAULT_SETTINGS.AGENT,
    language: DEFAULT_SETTINGS.LANGUAGE,
    confirmation_mode: DEFAULT_SETTINGS.CONFIRMATION_MODE,
    security_analyzer: DEFAULT_SETTINGS.SECURITY_ANALYZER,
  },
};

const openHandsHandlers = [
  http.get("/api/options/models", async () =>
    HttpResponse.json([
      "gpt-3.5-turbo",
      "gpt-4o",
      "anthropic/claude-3.5",
      "anthropic/claude-3-5-sonnet-20241022",
    ]),
  ),

  http.get("/api/options/agents", async () =>
    HttpResponse.json(["CodeActAgent", "CoActAgent"]),
  ),

  http.get("/api/options/security-analyzers", async () =>
    HttpResponse.json(["mock-invariant"]),
  ),

  http.get("http://localhost:3001/api/list-files", async ({ request }) => {
    await delay();

    const token = request.headers
      .get("Authorization")
      ?.replace("Bearer", "")
      .trim();

    if (!token) return HttpResponse.json([], { status: 401 });
    return HttpResponse.json(["file1.ts", "dir1/file2.ts", "file3.ts"]);
  }),

  http.post("http://localhost:3001/api/save-file", () =>
    HttpResponse.json(null, { status: 200 }),
  ),

  http.get("http://localhost:3001/api/select-file", async ({ request }) => {
    await delay();

    const token = request.headers
      .get("Authorization")
      ?.replace("Bearer", "")
      .trim();

    if (!token) {
      return HttpResponse.json([], { status: 401 });
    }

    const url = new URL(request.url);
    const file = url.searchParams.get("file")?.toString();

    if (file) {
      return HttpResponse.json({ code: `Content of ${file}` });
    }

    return HttpResponse.json(null, { status: 404 });
  }),

  http.post("http://localhost:3001/api/submit-feedback", async () => {
    await delay(1200);

    return HttpResponse.json({
      statusCode: 200,
      body: { message: "Success", link: "fake-url.com", password: "abc123" },
    });
  }),
];

export const handlers = [
  ...openHandsHandlers,
  http.get("https://api.github.com/user/repos", async ({ request }) => {
    const token = request.headers
      .get("Authorization")
      ?.replace("Bearer", "")
      .trim();

    if (!token) {
      return HttpResponse.json([], { status: 401 });
    }

    return HttpResponse.json([
      { id: 1, full_name: "octocat/hello-world" },
      { id: 2, full_name: "octocat/earth" },
    ]);
  }),
  http.get("https://api.github.com/user", () => {
    const user: GitHubUser = {
      id: 1,
      login: "octocat",
      avatar_url: "https://avatars.githubusercontent.com/u/583231?v=4",
      company: "GitHub",
      email: "placeholder@placeholder.placeholder",
      name: "monalisa octocat",
    };

    return HttpResponse.json(user);
  }),
  http.post("http://localhost:3001/api/submit-feedback", async () =>
    HttpResponse.json({ statusCode: 200 }, { status: 200 }),
  ),
  http.post("https://us.i.posthog.com/e", async () =>
    HttpResponse.json(null, { status: 200 }),
  ),
  http.get("/api/options/config", () => {
    const config: GetConfigResponse = {
      APP_MODE: "oss",
      GITHUB_CLIENT_ID: "fake-github-client-id",
      POSTHOG_CLIENT_KEY: "fake-posthog-client-key",
    };

    return HttpResponse.json(config);
  }),
  http.get("/api/settings", async () =>
    HttpResponse.json(userPreferences.settings),
  ),
  http.post("/api/settings", async ({ request }) => {
    const body = await request.json();

    if (body) {
      userPreferences.settings = {
        ...userPreferences.settings,
        // @ts-expect-error - We know this is a settings object
        ...body,
      };

      return HttpResponse.json(null, { status: 200 });
    }

    return HttpResponse.json(null, { status: 400 });
  }),
];
