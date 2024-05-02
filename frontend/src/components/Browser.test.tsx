import React from "react";
import Browser from "./Browser";
import { renderWithProviders } from "../../test-utils";

describe("Browser", () => {
  it("renders a message if no screenshotSrc is provided", () => {
    const { getByText } = renderWithProviders(<Browser />, {
      preloadedState: {
        browser: {
          url: "https://example.com",
          screenshotSrc: "",
        },
      },
    });

    // i18n empty message key
    expect(getByText(/BROWSER\$EMPTY_MESSAGE/i)).toBeInTheDocument();
  });

  it("renders the url and a screenshot", () => {
    const { getByText, getByAltText } = renderWithProviders(<Browser />, {
      preloadedState: {
        browser: {
          url: "https://example.com",
          screenshotSrc:
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN0uGvyHwAFCAJS091fQwAAAABJRU5ErkJggg==",
        },
      },
    });

    expect(getByText("https://example.com")).toBeInTheDocument();
    expect(getByAltText(/browser screenshot/i)).toBeInTheDocument();
  });
});
