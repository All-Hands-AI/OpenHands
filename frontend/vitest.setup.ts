import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "#/mocks/node";
import "@testing-library/jest-dom/vitest";

// @ts-expect-error - Mock for Terminal tests
HTMLCanvasElement.prototype.getContext = vi.fn();

// Mock the i18n provider
vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({ t: (key: string) => key }),
}));

// Mock requests during tests
beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  // Cleanup the document body after each test
  cleanup();
});
afterAll(() => server.close());
