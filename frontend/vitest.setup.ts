import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "#/mocks/node";
import "@testing-library/jest-dom/vitest";
import React from "react";

HTMLCanvasElement.prototype.getContext = vi.fn();
HTMLElement.prototype.scrollTo = vi.fn();

// Mock specific SVG imports to prevent issues with SVG loading in tests
vi.mock("#/icons/loading-outer.svg?react", () => ({
  default: () => React.createElement("div", { "data-testid": "mock-svg" }),
}));

vi.mock("./state-indicators/cold.svg?react", () => ({
  default: () => React.createElement("div", { "data-testid": "mock-svg-cold" }),
  virtual: true
}));

vi.mock("./state-indicators/running.svg?react", () => ({
  default: () => React.createElement("div", { "data-testid": "mock-svg-running" }),
  virtual: true
}));

// Mock the i18n provider
vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: "en",
      exists: () => false,
    },
  }),
}));

// Mock requests during tests
beforeAll(() => server.listen({ onUnhandledRequest: "bypass" }));
afterEach(() => {
  server.resetHandlers();
  // Cleanup the document body after each test
  cleanup();
});
afterAll(() => server.close());
