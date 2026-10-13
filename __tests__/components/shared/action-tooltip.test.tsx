import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ActionTooltip } from "#/components/shared/action-tooltip";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("#/components/shared/buttons/styled-tooltip", () => ({
  StyledTooltip: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

describe("ActionTooltip", () => {
  it("renders reject button with whitespace-nowrap and accessible name", async () => {
    const handleClick = vi.fn();
    render(<ActionTooltip type="reject" onClick={handleClick} />);

    const button = screen.getByTestId("action-reject-button");
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-label", "ACTION$REJECT");
    expect(button.className).toContain("whitespace-nowrap");

    const user = userEvent.setup();
    await user.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("renders confirm button with whitespace-nowrap and accessible name", async () => {
    const handleClick = vi.fn();
    render(<ActionTooltip type="confirm" onClick={handleClick} />);

    const button = screen.getByTestId("action-confirm-button");
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-label", "ACTION$CONFIRM");
    expect(button.className).toContain("whitespace-nowrap");

    const user = userEvent.setup();
    await user.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
