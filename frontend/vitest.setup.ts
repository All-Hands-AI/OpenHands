import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "#/mocks/node";
import "@testing-library/jest-dom/vitest";

// @ts-expect-error - Mock for Terminal tests
HTMLCanvasElement.prototype.getContext = vi.fn();

// @ts-expect-error - handle TypeError: dom.scrollTo is not a function
HTMLElement.prototype.scrollTo = vi.fn();

// Mock the i18n provider
vi.mock("react-i18next", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-i18next")>();
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        // Load the actual translations
        const translations = require("./src/i18n/translation.json");
        if (!translations[key] || !translations[key]["en"]) {
          throw new Error(`Missing translation for key: ${key}`);
        }
        return translations[key]["en"];
      },
      i18n: {
        language: "en",
        exists: (key: string) => {
          const translations = require("./src/i18n/translation.json");
          return !!translations[key];
        },
      },
    }),
  };
});

// Mock requests during tests
beforeAll(() => server.listen({ onUnhandledRequest: "bypass" }));
afterEach(() => {
  server.resetHandlers();
  // Cleanup the document body after each test
  cleanup();
});
afterAll(() => server.close());
