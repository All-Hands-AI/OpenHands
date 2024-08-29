import React from "react";
import { screen } from "@testing-library/react";
import Browser from "./Browser";
import { renderWithProviders } from "../../test-utils";

describe("Browser", () => {
  it("renders a message if no screenshotSrc is provided", () => {
    renderWithProviders(<Browser />);

    // i18n empty message key
    expect(screen.getByText("BROWSER$EMPTY_MESSAGE")).toBeInTheDocument();
  });

  it("renders the url and a screenshot", () => {
    renderWithProviders(<Browser />);

    expect(screen.getByText("https://example.com")).toBeInTheDocument();
    expect(screen.getByAltText(/browser screenshot/i)).toBeInTheDocument();
  });
});
