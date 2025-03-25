import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { UserAvatar } from "#/components/features/sidebar/user-avatar";

describe("UserAvatar", () => {
  const onClickMock = vi.fn();

  afterEach(() => {
    onClickMock.mockClear();
  });

  it("(default) should render the placeholder avatar when the user is logged out", () => {
    render(<UserAvatar onClick={onClickMock} />);
    expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
    expect(
      screen.getByLabelText("USER$AVATAR_PLACEHOLDER"),
    ).toBeInTheDocument();
  });

  it("should call onClick when clicked", async () => {
    const user = userEvent.setup();
    render(<UserAvatar onClick={onClickMock} />);

    const userAvatarContainer = screen.getByTestId("user-avatar");
    await user.click(userAvatarContainer);

    expect(onClickMock).toHaveBeenCalledOnce();
  });

  it("should display the user's avatar when available", () => {
    render(
      <UserAvatar
        onClick={onClickMock}
        avatarUrl="https://example.com/avatar.png"
      />,
    );

    expect(screen.getByAltText("AVATAR$ALT_TEXT")).toBeInTheDocument();
    expect(
      screen.queryByLabelText("USER$AVATAR_PLACEHOLDER"),
    ).not.toBeInTheDocument();
  });

  it("should display a loading spinner instead of an avatar when isLoading is true", () => {
    const { rerender } = render(<UserAvatar onClick={onClickMock} />);
    expect(screen.queryByTestId("loading-spinner")).not.toBeInTheDocument();
    expect(
      screen.getByLabelText("USER$AVATAR_PLACEHOLDER"),
    ).toBeInTheDocument();

    rerender(<UserAvatar onClick={onClickMock} isLoading />);
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    expect(
      screen.queryByLabelText("USER$AVATAR_PLACEHOLDER"),
    ).not.toBeInTheDocument();

    rerender(
      <UserAvatar
        onClick={onClickMock}
        avatarUrl="https://example.com/avatar.png"
        isLoading
      />,
    );
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    expect(screen.queryByAltText("AVATAR$ALT_TEXT")).not.toBeInTheDocument();
  });
});
