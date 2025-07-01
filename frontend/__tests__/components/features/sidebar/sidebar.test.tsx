import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { waitFor } from "@testing-library/react";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import OpenHands from "#/api/open-hands";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UserActions } from "#/components/features/sidebar/user-actions";

// These tests will now fail because the conversation panel is rendered through a portal
// and technically not a child of the Sidebar component.

const RouterStub = createRoutesStub([
  {
    path: "/conversation/:conversationId",
    Component: () => <Sidebar />,
  },
]);

const renderSidebar = () =>
  renderWithProviders(<RouterStub initialEntries={["/conversation/123"]} />);

describe("Sidebar", () => {
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch settings data on mount", async () => {
    renderSidebar();
    await waitFor(() => expect(getSettingsSpy).toHaveBeenCalled());
  });
});

describe.only("UserActions", () => {
  const user = userEvent.setup();
  const onLogoutMock = vi.fn();

  afterEach(() => {
    onLogoutMock.mockClear();
  });

  describe("Rendering", () => {
    it("should render user actions container and avatar", () => {
      render(<UserActions onLogout={onLogoutMock} />);

      expect(screen.getByTestId("user-actions")).toBeInTheDocument();
      expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
    });

    it("should render with loading state", () => {
      render(<UserActions onLogout={onLogoutMock} isLoading={true} />);

      expect(screen.getByTestId("user-actions")).toBeInTheDocument();
      expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
    });
  });

  describe("Context Menu Visibility - Critical User-Dependent Behavior", () => {
    it("should NOT show context menu when user is undefined and avatar is clicked", async () => {
      render(<UserActions onLogout={onLogoutMock} />);

      const userAvatar = screen.getByTestId("user-avatar");
      await user.click(userAvatar);

      // Context menu should NOT appear because user is undefined
      expect(
        screen.queryByTestId("account-settings-context-menu"),
      ).not.toBeInTheDocument();
    });

    it("should show context menu when user is provided and avatar is clicked", async () => {
      render(
        <UserActions
          onLogout={onLogoutMock}
          user={{ avatar_url: "https://example.com/avatar.png" }}
        />,
      );

      const userAvatar = screen.getByTestId("user-avatar");
      await user.click(userAvatar);

      // Context menu SHOULD appear because user is provided
      expect(
        screen.getByTestId("account-settings-context-menu"),
      ).toBeInTheDocument();
    });

    it("should show context menu even when user has no avatar_url", async () => {
      render(<UserActions onLogout={onLogoutMock} user={{ avatar_url: "" }} />);

      const userAvatar = screen.getByTestId("user-avatar");
      await user.click(userAvatar);

      // Context menu SHOULD appear because user object exists (even with empty avatar_url)
      expect(
        screen.getByTestId("account-settings-context-menu"),
      ).toBeInTheDocument();
    });
  });

  describe("Context Menu Toggle Behavior (when user is provided)", () => {
    it("should toggle context menu visibility when avatar is clicked multiple times", async () => {
      render(
        <UserActions
          onLogout={onLogoutMock}
          user={{ avatar_url: "https://example.com/avatar.png" }}
        />,
      );

      const userAvatar = screen.getByTestId("user-avatar");

      // First click - should show menu
      await user.click(userAvatar);
      expect(
        screen.getByTestId("account-settings-context-menu"),
      ).toBeInTheDocument();

      // Second click - should hide menu
      await user.click(userAvatar);
      expect(
        screen.queryByTestId("account-settings-context-menu"),
      ).not.toBeInTheDocument();

      // Third click - should show menu again
      await user.click(userAvatar);
      expect(
        screen.getByTestId("account-settings-context-menu"),
      ).toBeInTheDocument();
    });
  });

  describe("Logout Functionality", () => {
    it("should call onLogout and close menu when logout is clicked (user provided)", async () => {
      render(
        <UserActions
          onLogout={onLogoutMock}
          user={{ avatar_url: "https://example.com/avatar.png" }}
        />,
      );

      const userAvatar = screen.getByTestId("user-avatar");
      await user.click(userAvatar);

      const logoutOption = screen.getByText("ACCOUNT_SETTINGS$LOGOUT");
      await user.click(logoutOption);

      expect(onLogoutMock).toHaveBeenCalledOnce();
      expect(
        screen.queryByTestId("account-settings-context-menu"),
      ).not.toBeInTheDocument();
    });

    it("should NOT be able to access logout when no user is provided", async () => {
      render(<UserActions onLogout={onLogoutMock} />);

      const userAvatar = screen.getByTestId("user-avatar");
      await user.click(userAvatar);

      // Logout option should not be accessible because context menu doesn't appear
      expect(
        screen.queryByText("ACCOUNT_SETTINGS$LOGOUT"),
      ).not.toBeInTheDocument();
      expect(onLogoutMock).not.toHaveBeenCalled();
    });
  });

  describe("Edge Cases", () => {
    it("should handle user prop changing from undefined to defined", () => {
      const { rerender } = render(<UserActions onLogout={onLogoutMock} />);

      // Initially no user - context menu shouldn't work
      expect(
        screen.queryByTestId("account-settings-context-menu"),
      ).not.toBeInTheDocument();

      // Add user prop
      rerender(
        <UserActions
          onLogout={onLogoutMock}
          user={{ avatar_url: "https://example.com/avatar.png" }}
        />,
      );

      // Component should still render correctly
      expect(screen.getByTestId("user-actions")).toBeInTheDocument();
      expect(screen.getByTestId("user-avatar")).toBeInTheDocument();
    });

    it("should handle user prop changing from defined to undefined", async () => {
      const { rerender } = render(
        <UserActions
          onLogout={onLogoutMock}
          user={{ avatar_url: "https://example.com/avatar.png" }}
        />,
      );

      // Click to open menu
      const userAvatar = screen.getByTestId("user-avatar");
      await user.click(userAvatar);
      expect(
        screen.getByTestId("account-settings-context-menu"),
      ).toBeInTheDocument();

      // Remove user prop - menu should disappear
      rerender(<UserActions onLogout={onLogoutMock} />);

      expect(
        screen.queryByTestId("account-settings-context-menu"),
      ).not.toBeInTheDocument();
    });

    it("should work with loading state and user provided", async () => {
      render(
        <UserActions
          onLogout={onLogoutMock}
          user={{ avatar_url: "https://example.com/avatar.png" }}
          isLoading={true}
        />,
      );

      const userAvatar = screen.getByTestId("user-avatar");
      await user.click(userAvatar);

      // Context menu should still appear even when loading
      expect(
        screen.getByTestId("account-settings-context-menu"),
      ).toBeInTheDocument();
    });
  });
});
