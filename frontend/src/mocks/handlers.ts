import { delay, http, HttpResponse } from "msw";

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
  http.get("/config.json", () => HttpResponse.json({ APP_MODE: "oss" })),
];
