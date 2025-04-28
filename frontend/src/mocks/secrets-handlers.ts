import { http, HttpResponse } from "msw";

const DEFAULT_SECRETS = ["OpenAI_API_Key", "Google_Maps_API_Key"];
const secrets = new Map<string, string>(
  DEFAULT_SECRETS.map((secret) => [secret, "test-123"]),
);

export const SECRETS_HANDLERS = [
  http.get("/api/secrets", async () =>
    HttpResponse.json({
      custom_secrets: Array.from(secrets.keys()),
    }),
  ),

  http.post("/api/secrets", async ({ request }) => {
    const body = await request.json();
    if (typeof body === "object" && body?.name && body.value) {
      secrets.set(body.name, body.value);
      return HttpResponse.json(true);
    }

    return HttpResponse.json(false, { status: 400 });
  }),

  http.put("/api/secrets/:id", async ({ params, request }) => {
    const { id } = params;
    const body = await request.json();

    if (typeof id === "string" && typeof body === "object") {
      const secret = secrets.get(id);
      if (secret && body?.name && body.value) {
        secrets.delete(id);
        secrets.set(body.name, body.value);
        return HttpResponse.json(true);
      }
    }

    return HttpResponse.json(false, { status: 400 });
  }),

  http.delete("/api/secrets/:id", async ({ params }) => {
    const { id } = params;

    if (typeof id === "string") {
      secrets.delete(id);
      return HttpResponse.json(true);
    }

    return HttpResponse.json(false, { status: 400 });
  }),
];
