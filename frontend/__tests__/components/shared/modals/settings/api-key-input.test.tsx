import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { APIKeyInput } from "#/components/shared/inputs/api-key-input";

describe("APIKeyInput", () => {
  const onUnsetMock = vi.fn();

  it("should render an unset badge if the API key is not set", async () => {
    render(
      <APIKeyInput isDisabled={false} isSet={false} onUnset={onUnsetMock} />,
    );

    screen.getByText("unset");
    screen.getByTestId("api-key-input");
    expect(
      screen.queryByTestId("unset-api-key-button"),
    ).not.toBeInTheDocument();
  });

  it("should render a set badge if the API key is set", async () => {
    render(<APIKeyInput isDisabled={false} isSet onUnset={onUnsetMock} />);

    screen.getByText("set");
    expect(screen.queryByTestId("api-key-input")).not.toBeInTheDocument();
    screen.getByTestId("unset-api-key-button");
  });

  it("should call onUnset when the unset button is clicked", async () => {
    const user = userEvent.setup();
    render(<APIKeyInput isDisabled={false} isSet onUnset={onUnsetMock} />);

    const button = screen.getByTestId("unset-api-key-button");
    await user.click(button);

    expect(onUnsetMock).toHaveBeenCalledOnce();
  });
});
