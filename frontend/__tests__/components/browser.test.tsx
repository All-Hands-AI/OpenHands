import { screen } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import * as router from "react-router";
import { renderWithProviders } from "../../test-utils";
import { BrowserPanel } from "#/components/features/browser/browser";


describe("Browser", () => {
  beforeEach(() => {
    vi.spyOn(router, "useParams").mockReturnValue({ conversationId: "test-conversation-id" });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });
  it("renders a message if no screenshotSrc is provided", () => {
    renderWithProviders(<BrowserPanel />, {
      preloadedState: {
        browser: {
          url: "https://example.com",
          screenshotSrc: "",
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
        },
      },
    });

    expect(screen.getByText("https://example.com")).toBeInTheDocument();
    expect(screen.getByAltText(/browser screenshot/i)).toBeInTheDocument();
  });
});
