import { screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { createRoutesStub } from "react-router";
import App from "#/routes/_oh.app/route";
import { renderWithProviders } from "../../../test-utils";

describe("Collapsible Panel", () => {
  const RouteStub = createRoutesStub([{ Component: App, path: "/" }]);

  it("should start with expanded panel", () => {
    renderWithProviders(<RouteStub />);
    const rightPanel = screen.getByRole("complementary");
    expect(rightPanel).toHaveClass("grow");
    expect(rightPanel).not.toHaveClass("w-0");
  });

  it("should collapse panel when collapse button is clicked", () => {
    renderWithProviders(<RouteStub />);
    const collapseButton = screen.getByLabelText("Collapse panel");
    fireEvent.click(collapseButton);
    const rightPanel = screen.getByRole("complementary");
    expect(rightPanel).toHaveClass("w-0");
    expect(rightPanel).not.toHaveClass("grow");
  });

  it("should expand panel when expand button is clicked", () => {
    renderWithProviders(<RouteStub />);
    const collapseButton = screen.getByLabelText("Collapse panel");
    // First collapse
    fireEvent.click(collapseButton);
    // Then expand
    const expandButton = screen.getByLabelText("Expand panel");
    fireEvent.click(expandButton);
    const rightPanel = screen.getByRole("complementary");
    expect(rightPanel).toHaveClass("grow");
    expect(rightPanel).not.toHaveClass("w-0");
  });

  it("should adjust chat panel width when right panel is collapsed", () => {
    renderWithProviders(<RouteStub />);
    const chatPanel = screen.getByTestId("chat-panel");
    expect(chatPanel).toHaveClass("w-[390px]");
    const collapseButton = screen.getByLabelText("Collapse panel");
    fireEvent.click(collapseButton);
    expect(chatPanel).toHaveClass("w-full");
  });
});
