import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/options/models", () => HttpResponse.json([])),
  http.get("/api/options/agents", () => HttpResponse.json([])),
];
