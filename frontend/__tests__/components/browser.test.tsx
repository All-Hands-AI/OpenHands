import { describe, it, expect, afterEach, vi } from "vitest";

// Mock useParams before importing components
vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...(actual as object),
    useParams: () => ({ conversationId: "test-conversation-id" }),
  };
});

// Mock i18next
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...(actual as object),
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
import * as BrowserService from "#/services/context-services/browser-service";

describe("Browser", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });
  it("renders a message if no screenshotSrc is provided", () => {
    // Mock the browser service
    vi.spyOn(BrowserService, "getUrl").mockReturnValue("https://example.com");
    vi.spyOn(BrowserService, "getScreenshotSrc").mockReturnValue("");
    
    renderWithProviders(<BrowserPanel />);

    // i18n empty message key
    expect(screen.getByText("BROWSER$NO_PAGE_LOADED")).toBeInTheDocument();
  });

  it("renders the url from the browser context", () => {
    // Mock the browser service
    vi.spyOn(BrowserService, "getUrl").mockReturnValue("https://github.com/All-Hands-AI/OpenHands");
    vi.spyOn(BrowserService, "getScreenshotSrc").mockReturnValue("");
    
    renderWithProviders(<BrowserPanel />);

    expect(screen.getByText("https://github.com/All-Hands-AI/OpenHands")).toBeInTheDocument();
  });
});
