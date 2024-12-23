import { delay, http, HttpResponse } from "msw";
import { Conversation } from "#/api/open-hands.types";

const conversations: Conversation[] = [
  {
    conversation_id: "1",
    name: "My New Project",
    repo: null,
    lastUpdated: new Date().toISOString(),
    state: "running",
  },
  {
    conversation_id: "2",
    name: "Repo Testing",
    repo: "octocat/hello-world",
    // 2 days ago
    lastUpdated: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    state: "cold",
  },
  {
    conversation_id: "3",
    name: "Another Project",
    repo: "octocat/earth",
    // 5 days ago
    lastUpdated: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    state: "finished",
  },
];

const CONVERSATIONS = new Map<string, Conversation>(
  conversations.map((conversation) => [
    conversation.conversation_id,
    conversation,
  ]),
);

const openHandsHandlers = [
  http.get("/api/options/models", async () => {
    await delay();
    return HttpResponse.json([
      "gpt-3.5-turbo",
      "gpt-4o",
      "anthropic/claude-3.5",
    ]);
  }),

  http.get("/api/options/agents", async () => {
    await delay();
    return HttpResponse.json(["CodeActAgent", "CoActAgent"]);
  }),

  http.get("/api/options/security-analyzers", async () => {
    await delay();
    return HttpResponse.json(["mock-invariant"]);
  }),

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
  ...openHandsHandlers,
  http.get("/api/github/repositories", () =>
    HttpResponse.json([
      { id: 1, full_name: "octocat/hello-world" },
      { id: 2, full_name: "octocat/earth" },
    ]),
  ),
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

  http.post("/api/authenticate", async () =>
    HttpResponse.json({ message: "Authenticated" }),
  ),

  http.get("/api/options/config", () => HttpResponse.json({ APP_MODE: "oss" })),

  http.get("/api/conversations", async () =>
    HttpResponse.json(Array.from(CONVERSATIONS.values())),
  ),

  http.delete("/api/conversations/:conversationId", async ({ params }) => {
    const { conversationId } = params;

    if (typeof conversationId === "string") {
      CONVERSATIONS.delete(conversationId);
      return HttpResponse.json(null, { status: 200 });
    }

    return HttpResponse.json(null, { status: 404 });
  }),

  http.put(
    "/api/conversations/:conversationId",
    async ({ params, request }) => {
      const { conversationId } = params;

      if (typeof conversationId === "string") {
        const conversation = CONVERSATIONS.get(conversationId);

        if (conversation) {
          const body = await request.json();
          if (typeof body === "object" && body?.name) {
            CONVERSATIONS.set(conversationId, {
              ...conversation,
              name: body.name,
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
      name: "New Conversation",
      repo: null,
      lastUpdated: new Date().toISOString(),
      state: "warm",
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
];
