import React from "react";
import Browser from "./Browser";
import { renderWithProviders } from "../../test-utils";

describe("Browser", () => {
  it("renders a message if no screenshotSrc is provided", () => {
    const { getByText, getByAltText } = renderWithProviders(<Browser />, {
      preloadedState: {
        browser: {
          url: "https://example.com",
          screenshotSrc: "",
        },
      },
    });

    expect(getByText(/OpenDevin: Code Less, Make More./i)).toBeInTheDocument();
    expect(getByAltText(/Blank Page/i)).toBeInTheDocument();
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
