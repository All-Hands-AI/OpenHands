import { describe, it, expect, afterEach, vi } from "vitest";
import * as router from "react-router";

// Mock useParams before importing components
vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual as object,
    useParams: () => ({ conversationId: "test-conversation-id" }),
  };
});

// Mock i18next
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual as object,
    useTranslation: () => ({
      t: (key: string) => key,
      i18n: {
        changeLanguage: () => new Promise(() => {}),
      },
    }),
  };
});

import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils";
import { BrowserPanel } from "#/components/features/browser/browser";


describe("Browser", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });
  it("renders a message if no screenshotSrc is provided", () => {
    renderWithProviders(<BrowserPanel />, {
      preloadedState: {
        browser: {
          url: "https://example.com",
          screenshotSrc: "",
          updateCount: 0,
        },
      },
    });

    // i18n empty message key
    expect(screen.getByText("BROWSER$EMPTY_MESSAGE")).toBeInTheDocument();
  });

  it("renders the url and a screenshot", () => {
    renderWithProviders(<BrowserPanel />, {
      preloadedState: {
        browser: {
          url: "https://example.com",
          screenshotSrc:
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN0uGvyHwAFCAJS091fQwAAAABJRU5ErkJggg==",
          updateCount: 0,
        },
      },
    });

    expect(screen.getByText("https://example.com")).toBeInTheDocument();
    expect(screen.getByAltText(/browser screenshot/i)).toBeInTheDocument();
  });
});
