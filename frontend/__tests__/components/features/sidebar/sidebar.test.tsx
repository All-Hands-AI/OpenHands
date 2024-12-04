import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { AuthProvider } from "#/context/auth-context";
import { UserPrefsProvider } from "#/context/user-prefs-context";

const renderSidebar = () =>
  render(<Sidebar />, {
    wrapper: ({ children }) => (
      <AuthProvider>
        <QueryClientProvider client={new QueryClient()}>
          <UserPrefsProvider>{children}</UserPrefsProvider>
        </QueryClientProvider>
      </AuthProvider>
    ),
  });

describe("Sidebar", () => {
  vi.mock("react-router", async (importOriginal) => ({
    ...(await importOriginal<typeof import("react-router")>()),
    useSearchParams: vi.fn(() => [{ get: vi.fn() }]),
    useLocation: vi.fn(),
    useNavigate: vi.fn(),
  }));

  it("should toggle the project panel", async () => {
    const user = userEvent.setup();
    renderSidebar();

    expect(screen.queryByTestId("project-panel")).not.toBeInTheDocument();
    const projectPanelButton = screen.getByTestId("toggle-project-panel");

    await user.click(projectPanelButton);

    expect(screen.getByTestId("project-panel")).toBeInTheDocument();
  });
});
