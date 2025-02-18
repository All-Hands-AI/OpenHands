import { delay, http, HttpResponse } from "msw";
import {
  GetConfigResponse,
  Conversation,
  ResultSet,
} from "#/api/open-hands.types";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { STRIPE_BILLING_HANDLERS } from "./billing-handlers";
import { ApiSettings, PostApiSettings } from "#/types/settings";

export const MOCK_DEFAULT_USER_SETTINGS: ApiSettings | PostApiSettings = {
  llm_model: DEFAULT_SETTINGS.LLM_MODEL,
  llm_base_url: DEFAULT_SETTINGS.LLM_BASE_URL,
  llm_api_key: DEFAULT_SETTINGS.LLM_API_KEY,
  agent: DEFAULT_SETTINGS.AGENT,
  language: DEFAULT_SETTINGS.LANGUAGE,
  confirmation_mode: DEFAULT_SETTINGS.CONFIRMATION_MODE,
  security_analyzer: DEFAULT_SETTINGS.SECURITY_ANALYZER,
  remote_runtime_resource_factor:
    DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
  github_token_is_set: DEFAULT_SETTINGS.GITHUB_TOKEN_IS_SET,
  enable_default_condenser: DEFAULT_SETTINGS.ENABLE_DEFAULT_CONDENSER,
  user_consents_to_analytics: DEFAULT_SETTINGS.USER_CONSENTS_TO_ANALYTICS,
};

const MOCK_USER_PREFERENCES: {
  settings: ApiSettings | PostApiSettings;
} = {
  settings: MOCK_DEFAULT_USER_SETTINGS,
};

const conversations: Conversation[] = [
  {
    conversation_id: "1",
    title: "My New Project",
    selected_repository: null,
    last_updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    status: "RUNNING",
  },
  {
    conversation_id: "2",
    title: "Repo Testing",
    selected_repository: "octocat/hello-world",
    // 2 days ago
    last_updated_at: new Date(
      Date.now() - 2 * 24 * 60 * 60 * 1000,
    ).toISOString(),
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    status: "STOPPED",
  },
  {
    conversation_id: "3",
    title: "Another Project",
    selected_repository: "octocat/earth",
    // 5 days ago
    last_updated_at: new Date(
      Date.now() - 5 * 24 * 60 * 60 * 1000,
    ).toISOString(),
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    status: "STOPPED",
  },
];

const CONVERSATIONS = new Map<string, Conversation>(
  conversations.map((conversation) => [
    conversation.conversation_id,
    conversation,
  ]),
);

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

  http.get(
    "http://localhost:3001/api/conversations/:conversationId/list-files",
    async ({ params }) => {
      await delay();

      const cid = params.conversationId?.toString();
      if (!cid) return HttpResponse.json([], { status: 404 });

      let data = ["file1.txt", "file2.txt", "file3.txt"];
      if (cid === "3") {
        data = [
          "reboot_skynet.exe",
          "target_list.txt",
          "terminator_blueprint.txt",
        ];
      }

      return HttpResponse.json(data);
    },
  ),

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
  ...STRIPE_BILLING_HANDLERS,
  ...openHandsHandlers,
  http.get("/api/github/repositories", () =>
    HttpResponse.json([
      { id: 1, full_name: "octocat/hello-world" },
      { id: 2, full_name: "octocat/earth" },
    ]),
  ),
  http.get("/api/github/user", () => {
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
    const mockSaas = import.meta.env.VITE_MOCK_SAAS === "true";
    const config: GetConfigResponse = {
      APP_MODE: mockSaas ? "saas" : "oss",
      GITHUB_CLIENT_ID: "fake-github-client-id",
      POSTHOG_CLIENT_KEY: "fake-posthog-client-key",
    };

    return HttpResponse.json(config);
  }),
  http.get("/api/settings", async () => {
    await delay();
    const settings: ApiSettings = {
      ...MOCK_USER_PREFERENCES.settings,
      language: "no",
    };
    // @ts-expect-error - mock types
    if (settings.github_token) settings.github_token_is_set = true;

    return HttpResponse.json(settings);
  }),
  http.post("/api/settings", async ({ request }) => {
    const body = await request.json();

    if (body) {
      let newSettings: Partial<PostApiSettings> = {};
      if (typeof body === "object") {
        newSettings = { ...body };
        if (newSettings.unset_github_token) {
          newSettings.github_token = undefined;
          newSettings.github_token_is_set = false;
          delete newSettings.unset_github_token;
        }
      }

      MOCK_USER_PREFERENCES.settings = {
        ...MOCK_USER_PREFERENCES.settings,
        ...newSettings,
      };

      return HttpResponse.json(null, { status: 200 });
    }

    return HttpResponse.json(null, { status: 400 });
  }),

  http.post("/api/authenticate", async () =>
    HttpResponse.json({ message: "Authenticated" }),
  ),

  http.get("/api/options/config", () => HttpResponse.json({ APP_MODE: "oss" })),

  http.get("/api/conversations", async () => {
    const values = Array.from(CONVERSATIONS.values());
    const results: ResultSet<Conversation> = {
      results: values,
      next_page_id: null,
    };

    return HttpResponse.json(results, { status: 200 });
  }),

  http.delete("/api/conversations/:conversationId", async ({ params }) => {
    const { conversationId } = params;

    if (typeof conversationId === "string") {
      CONVERSATIONS.delete(conversationId);
      return HttpResponse.json(null, { status: 200 });
    }

    return HttpResponse.json(null, { status: 404 });
  }),

  http.patch(
    "/api/conversations/:conversationId",
    async ({ params, request }) => {
      const { conversationId } = params;

      if (typeof conversationId === "string") {
        const conversation = CONVERSATIONS.get(conversationId);

        if (conversation) {
          const body = await request.json();
          if (typeof body === "object" && body?.title) {
            CONVERSATIONS.set(conversationId, {
              ...conversation,
              title: body.title,
            });
            return HttpResponse.json(null, { status: 200 });
          }
        }
      }

      return HttpResponse.json(null, { status: 404 });
    },
  ),

  http.post("/api/conversations", () => {
    const conversation: Conversation = {
      conversation_id: (Math.random() * 100).toString(),
      title: "New Conversation",
      selected_repository: null,
      last_updated_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      status: "RUNNING",
    };

    CONVERSATIONS.set(conversation.conversation_id, conversation);
    return HttpResponse.json(conversation, { status: 201 });
  }),

  http.get("/api/conversations/:conversationId", async ({ params }) => {
    const { conversationId } = params;

    if (typeof conversationId === "string") {
      const project = CONVERSATIONS.get(conversationId);

      if (project) {
        return HttpResponse.json(project, { status: 200 });
      }
    }

    return HttpResponse.json(null, { status: 404 });
  }),

  http.post("/api/logout", () => HttpResponse.json(null, { status: 200 })),
];
