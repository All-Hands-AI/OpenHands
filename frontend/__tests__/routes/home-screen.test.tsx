import { render, screen } from "@testing-library/react";
import { describe, it } from "vitest";
import HomeScreen from "#/routes/new-home";

describe("HomeScreen", () => {
  it("should render", () => {
    render(<HomeScreen />);
    screen.getByTestId("home-screen");
  });
});
