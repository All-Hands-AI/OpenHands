import { describe, it, expect, afterEach, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils";
import { BrowserPanel } from "#/components/features/browser/browser";

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

const { useBrowserMock } = vi.hoisted(() => ({
  useBrowserMock: vi.fn(),
}));

vi.mock("#/hooks/state/use-browser", async () => ({
  useBrowser: useBrowserMock,
}));

describe("Browser", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders a message if no screenshotSrc is provided", () => {
    useBrowserMock.mockReturnValue({
      url: "https://example.com",
      screenshotSrc: "",
    });
    renderWithProviders(<BrowserPanel />);

    // i18n empty message key
    expect(screen.getByText("BROWSER$NO_PAGE_LOADED")).toBeInTheDocument();
  });

  it("renders the url and a screenshot", () => {
    useBrowserMock.mockReturnValue({
      url: "https://example.com",
      screenshotSrc:
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN0uGvyHwAFCAJS091fQwAAAABJRU5ErkJggg==",
    });
    renderWithProviders(<BrowserPanel />);

    expect(screen.getByText("https://example.com")).toBeInTheDocument();
    expect(screen.getByAltText(/browser screenshot/i)).toBeInTheDocument();
  });
});
