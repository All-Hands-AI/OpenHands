import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MCPServerList } from "../mcp-server-list";

// Mock react-i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const mockServers = [
  {
    id: "sse-0",
    type: "sse" as const,
    url: "https://very-long-url-that-could-cause-layout-overflow.example.com/api/v1/mcp/server/endpoint/with/many/path/segments",
  },
  {
    id: "stdio-0",
    type: "stdio" as const,
    name: "test-stdio-server",
    command: "python",
    args: ["-m", "test_server"],
  },
];

describe("MCPServerList", () => {
  it("should render servers with proper layout structure", () => {
    const mockOnEdit = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <MCPServerList
        servers={mockServers}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    // Check that the table structure is rendered
    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();
    expect(table).toHaveClass("w-full", "min-w-full", "table-fixed");

    // Check that the overflow container is present
    const overflowContainer = table.parentElement;
    expect(overflowContainer).toHaveClass("overflow-x-auto");

    // Check that server items are rendered
    const serverItems = screen.getAllByTestId("mcp-server-item");
    expect(serverItems).toHaveLength(2);

    // Check that action buttons are present for each server
    const editButtons = screen.getAllByTestId("edit-mcp-server-button");
    const deleteButtons = screen.getAllByTestId("delete-mcp-server-button");
    expect(editButtons).toHaveLength(2);
    expect(deleteButtons).toHaveLength(2);
  });

  it("should render empty state when no servers", () => {
    const mockOnEdit = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <MCPServerList
        servers={[]}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText("SETTINGS$MCP_NO_SERVERS")).toBeInTheDocument();
  });

  it("should handle long URLs without breaking layout", () => {
    const longUrlServer = {
      id: "sse-0",
      type: "sse" as const,
      url: "https://extremely-long-url-that-would-previously-cause-layout-overflow-and-push-action-buttons-out-of-view.example.com/api/v1/mcp/server/endpoint/with/many/path/segments/and/query/parameters?param1=value1&param2=value2&param3=value3",
    };

    const mockOnEdit = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <MCPServerList
        servers={[longUrlServer]}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    // Check that action buttons are still present and accessible
    const editButton = screen.getByTestId("edit-mcp-server-button");
    const deleteButton = screen.getByTestId("delete-mcp-server-button");

    expect(editButton).toBeInTheDocument();
    expect(deleteButton).toBeInTheDocument();

    // Check that the action column has proper flex-shrink-0 class to prevent shrinking
    const actionCell = editButton.closest("td");
    expect(actionCell).toHaveClass("flex-shrink-0");
  });
});
