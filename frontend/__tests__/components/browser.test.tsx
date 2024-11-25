import { screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { renderWithProviders } from "../../test-utils";
import BrowserPanel from "#/components/browser";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key === "browser.emptyMessage" ? "No browser content to display" : key,
  }),
}));

describe("Browser", () => {
  it("renders a message if no screenshotSrc is provided", () => {
    renderWithProviders(<BrowserPanel />, {
      preloadedState: {
        browser: {
          url: "https://example.com",
          screenshotSrc: "",
        },
      },
    });

    expect(screen.getByText("No browser content to display")).toBeInTheDocument();
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
