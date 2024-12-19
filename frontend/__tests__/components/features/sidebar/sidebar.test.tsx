import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { Sidebar } from "#/components/features/sidebar/sidebar";

const renderSidebar = () => renderWithProviders(<Sidebar />);

describe("Sidebar", () => {
  vi.mock("react-router", async (importOriginal) => ({
    ...(await importOriginal<typeof import("react-router")>()),
    useSearchParams: vi.fn(() => [{ get: vi.fn() }]),
    useLocation: vi.fn(() => ({ pathname: "/conversation" })),
    useNavigate: vi.fn(),
  }));

  it("should have the conversation panel open by default", () => {
    renderSidebar();

    expect(screen.getByTestId("conversation-panel")).toBeInTheDocument();
  });

  it("should toggle the conversation panel", async () => {
    const user = userEvent.setup();
    renderSidebar();

    const projectPanelButton = screen.getByTestId("toggle-conversation-panel");

    await user.click(projectPanelButton);

    expect(screen.queryByTestId("conversation-panel")).not.toBeInTheDocument();
  });
});
