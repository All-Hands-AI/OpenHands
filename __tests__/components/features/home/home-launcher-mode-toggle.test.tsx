import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { HomeLauncherModeToggle } from "#/components/features/home/home-launcher-mode-toggle";

describe("HomeLauncherModeToggle", () => {
  it("uses theme contrast token for active and hover states instead of hardcoded white", () => {
    const onChange = vi.fn();
    render(<HomeLauncherModeToggle mode="code" onChange={onChange} />);

    const codeButton = screen.getByTestId("home-launcher-mode-code");
    const automateButton = screen.getByTestId("home-launcher-mode-automate");

    // Active button must use contrast role and not hardcode white text
    expect(codeButton.className).toContain("text-[var(--oh-contrast)]");
    expect(codeButton.className).not.toContain("text-white");

    // Inactive button must use muted text with hover contrast role instead of hover:text-white
    expect(automateButton.className).toContain("text-[var(--oh-muted)]");
    expect(automateButton.className).toContain(
      "hover:text-[var(--oh-contrast)]",
    );
    expect(automateButton.className).not.toContain("hover:text-white");
  });

  it("updates classes correctly when mode is automate", () => {
    const onChange = vi.fn();
    render(<HomeLauncherModeToggle mode="automate" onChange={onChange} />);

    const codeButton = screen.getByTestId("home-launcher-mode-code");
    const automateButton = screen.getByTestId("home-launcher-mode-automate");

    expect(automateButton.className).toContain("text-[var(--oh-contrast)]");
    expect(automateButton.className).not.toContain("text-white");

    expect(codeButton.className).toContain("text-[var(--oh-muted)]");
    expect(codeButton.className).toContain("hover:text-[var(--oh-contrast)]");
    expect(codeButton.className).not.toContain("hover:text-white");
  });

  it("calls onChange when an inactive button is clicked", () => {
    const onChange = vi.fn();
    render(<HomeLauncherModeToggle mode="code" onChange={onChange} />);

    const automateButton = screen.getByTestId("home-launcher-mode-automate");
    fireEvent.click(automateButton);

    expect(onChange).toHaveBeenCalledWith("automate");
  });
});
