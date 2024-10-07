import { delay, http, HttpResponse } from "msw";

export const handlers = [
  http.get("https://api.github.com/user/repos", ({ request }) => {
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
  http.get("http://localhost:3000/api/list-files", async ({ request }) => {
    await delay();

    const token = request.headers
      .get("Authorization")
      ?.replace("Bearer", "")
      .trim();

    if (!token) {
      return HttpResponse.json([], { status: 401 });
    }

    return HttpResponse.json(["file1.ts", "dir1/file2.ts", "file3.ts"]);
  }),
  http.get("http://localhost:3000/api/select-file", async ({ request }) => {
    await delay(500);

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
  http.get("http://localhost:3000/api/options/agents", async () => {
    await delay();
    return HttpResponse.json(["CodeActAgent", "CoActAgent"]);
  }),
  http.get("http://localhost:3000/api/options/models", async () => {
    await delay();
    return HttpResponse.json([
      "gpt-3.5-turbo",
      "gpt-4o",
      "anthropic/claude-3.5",
    ]);
  }),
  http.post("http://localhost:3000/api/submit-feedback", async () =>
    HttpResponse.json({ statusCode: 200 }, { status: 200 }),
  ),
  http.post("http://localhost:3000/api/save-file", () =>
    HttpResponse.json(null, { status: 200 }),
  ),
  http.get("http://localhost:3000/api/options/security-analyzers", async () => {
    await delay();
    return HttpResponse.json(["mock-invariant"]);
  }),
];
