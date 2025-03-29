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

// Mock the useBrowser hook
vi.mock("#/hooks/query/use-browser", () => ({
  useBrowser: vi.fn(),
}));

import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils";
import { BrowserPanel } from "#/components/features/browser/browser";
import { useBrowser } from "#/hooks/query/use-browser";

describe("Browser", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });
  it("renders a message if no screenshotSrc is provided", () => {
    // Mock the hook to return empty screenshot
    (useBrowser as any).mockReturnValue({
      url: "https://github.com/All-Hands-AI/OpenHands",
      screenshotSrc: "",
      isLoading: false,
      setUrl: vi.fn(),
      setScreenshotSrc: vi.fn(),
    });

    renderWithProviders(<BrowserPanel />);

    // i18n empty message key
    expect(screen.getByText("BROWSER$NO_PAGE_LOADED")).toBeInTheDocument();
  });

  it("renders the url and a screenshot", () => {
    // Mock the hook to return a screenshot
    (useBrowser as any).mockReturnValue({
      url: "https://example.com",
      screenshotSrc: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN0uGvyHwAFCAJS091fQwAAAABJRU5ErkJggg==",
      isLoading: false,
      setUrl: vi.fn(),
      setScreenshotSrc: vi.fn(),
    });

    renderWithProviders(<BrowserPanel />);

    expect(screen.getByText("https://example.com")).toBeInTheDocument();
    expect(screen.getByAltText(/browser screenshot/i)).toBeInTheDocument();
  });
});
