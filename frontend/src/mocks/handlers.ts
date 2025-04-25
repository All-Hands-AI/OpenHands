import { delay, http, HttpResponse } from "msw";
import { GetConfigResponse } from "#/api/open-hands.types";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { STRIPE_BILLING_HANDLERS } from "./billing-handlers";
import { ApiSettings, PostApiSettings } from "#/types/settings";
import { CONVERSATION_HANDLERS } from "./conversation-handlers";
import { FILE_SERVICE_HANDLERS } from "./file-service-handlers";
import { GitRepository, GitUser } from "#/types/git";
import { TASK_SUGGESTIONS_HANDLERS } from "./task-suggestions-handlers";

export const MOCK_DEFAULT_USER_SETTINGS: ApiSettings | PostApiSettings = {
  llm_model: DEFAULT_SETTINGS.LLM_MODEL,
  llm_base_url: DEFAULT_SETTINGS.LLM_BASE_URL,
  llm_api_key: null,
  llm_api_key_set: DEFAULT_SETTINGS.LLM_API_KEY_SET,
  agent: DEFAULT_SETTINGS.AGENT,
  language: DEFAULT_SETTINGS.LANGUAGE,
  confirmation_mode: DEFAULT_SETTINGS.CONFIRMATION_MODE,
  security_analyzer: DEFAULT_SETTINGS.SECURITY_ANALYZER,
  remote_runtime_resource_factor:
    DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
  provider_tokens_set: DEFAULT_SETTINGS.PROVIDER_TOKENS_SET,
  enable_default_condenser: DEFAULT_SETTINGS.ENABLE_DEFAULT_CONDENSER,
  enable_sound_notifications: DEFAULT_SETTINGS.ENABLE_SOUND_NOTIFICATIONS,
  user_consents_to_analytics: DEFAULT_SETTINGS.USER_CONSENTS_TO_ANALYTICS,
  provider_tokens: DEFAULT_SETTINGS.PROVIDER_TOKENS,
};

const MOCK_USER_PREFERENCES: {
  settings: ApiSettings | PostApiSettings | null;
} = {
  settings: null,
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

  http.post("http://localhost:3001/api/submit-feedback", async () => {
    await delay(1200);

    return HttpResponse.json({
      statusCode: 200,
      body: { message: "Success", link: "fake-url.com", password: "abc123" },
    });
  }),
];

export const handlers = [
  ...STRIPE_BILLING_HANDLERS,
  ...CONVERSATION_HANDLERS,
  ...FILE_SERVICE_HANDLERS,
  ...TASK_SUGGESTIONS_HANDLERS,
  ...openHandsHandlers,
  http.get("/api/user/repositories", () => {
    const data: GitRepository[] = [
      {
        id: 1,
        full_name: "octocat/hello-world",
        git_provider: "github",
        is_public: true,
      },
      {
        id: 2,
        full_name: "octocat/earth",
        git_provider: "github",
        is_public: true,
      },
    ];

    return HttpResponse.json(data);
  }),
  http.get("/api/user/info", () => {
    const user: GitUser = {
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
    const mockSaas = import.meta.env.VITE_MOCK_SAAS === "true";

    const config: GetConfigResponse = {
      APP_MODE: mockSaas ? "saas" : "oss",
      GITHUB_CLIENT_ID: "fake-github-client-id",
      POSTHOG_CLIENT_KEY: "fake-posthog-client-key",
      STRIPE_PUBLISHABLE_KEY: "",
      FEATURE_FLAGS: {
        ENABLE_BILLING: mockSaas,
        HIDE_LLM_SETTINGS: mockSaas,
      },
    };

    return HttpResponse.json(config);
  }),
  http.get("/api/settings", async () => {
    await delay();

    const { settings } = MOCK_USER_PREFERENCES;

    if (!settings) return HttpResponse.json(null, { status: 404 });

    if (Object.keys(settings.provider_tokens_set).length > 0)
      settings.provider_tokens_set = { github: false, gitlab: false };

    return HttpResponse.json(settings);
  }),
  http.post("/api/settings", async ({ request }) => {
    const body = await request.json();

    if (body) {
      let newSettings: Partial<PostApiSettings> = {};
      if (typeof body === "object") {
        newSettings = { ...body };
      }

      const fullSettings = {
        ...MOCK_DEFAULT_USER_SETTINGS,
        ...MOCK_USER_PREFERENCES.settings,
        ...newSettings,
      };

      MOCK_USER_PREFERENCES.settings = fullSettings;
      return HttpResponse.json(null, { status: 200 });
    }

    return HttpResponse.json(null, { status: 400 });
  }),

  http.post("/api/authenticate", async () =>
    HttpResponse.json({ message: "Authenticated" }),
  ),

  http.get("/api/options/config", () => HttpResponse.json({ APP_MODE: "oss" })),


  http.post("/api/logout", () => HttpResponse.json(null, { status: 200 })),

  http.post("/api/reset-settings", async () => {
    await delay();
    MOCK_USER_PREFERENCES.settings = { ...MOCK_DEFAULT_USER_SETTINGS };
    return HttpResponse.json(null, { status: 200 });
  }),
];
