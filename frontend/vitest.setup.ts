import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "#/mocks/node";
import "@testing-library/jest-dom/vitest";
import React from "react";

HTMLCanvasElement.prototype.getContext = vi.fn();
HTMLElement.prototype.scrollTo = vi.fn();

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

// Mock the HydratedRouter component from react-router/dom
vi.mock("react-router/dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router/dom")>();
  const { createMemoryRouter, RouterProvider } = await import("react-router");
  
  return {
    ...actual,
    HydratedRouter: ({ children }: { children?: React.ReactNode }) => {
      const router = createMemoryRouter([
        {
          path: "/",
          element: children || null,
        },
      ]);
      
      return React.createElement(RouterProvider, { router });
    },
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
