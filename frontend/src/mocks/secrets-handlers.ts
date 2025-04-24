import { http, HttpResponse } from "msw";

export const SECRETS_HANDLERS = [
  http.get("/api/secrets", async () =>
    HttpResponse.json({
      custom_secrets: ["OpenAI API Key", "Google Maps API Key"],
    }),
  ),
];
