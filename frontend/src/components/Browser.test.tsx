import React from "react";
import { screen } from "@testing-library/react";
import Browser from "./Browser";
import { renderWithProviders } from "../../test-utils";

describe("Browser", () => {
  it("renders a message if no screenshotSrc is provided", () => {
    renderWithProviders(<Browser />, {
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
    renderWithProviders(<Browser />, {
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
