import { render, screen, fireEvent } from "@testing-library/react";
import { MicroagentSuggestions, MicroagentInfo } from "#/components/features/chat/microagent-suggestions";
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("MicroagentSuggestions", () => {
  const mockMicroagents: MicroagentInfo[] = [
    {
      name: "PR Update",
      trigger: "/pr_update",
      description: "Update a pull request",
    },
    {
      name: "PR Comment",
      trigger: "/pr_comment",
      description: "Comment on a pull request",
    },
    {
      name: "Test Update",
      trigger: "/update_test",
      description: "Update tests",
    },
  ];

  // Mock fetch
  beforeEach(() => {
    global.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockMicroagents),
      })
    );
  });

  it("should render microagent suggestions when visible", async () => {
    const onSelect = vi.fn();

    render(
      <MicroagentSuggestions
        query="/"
        isVisible={true}
        onSelect={onSelect}
      />
    );

    // Wait for the fetch to complete
    await vi.waitFor(() => {
      expect(screen.getByText("/pr_update")).toBeInTheDocument();
    });

    expect(screen.getByText("/pr_comment")).toBeInTheDocument();
    expect(screen.getByText("/update_test")).toBeInTheDocument();
  });

  it("should filter microagents based on query", async () => {
    const onSelect = vi.fn();

    const { rerender } = render(
      <MicroagentSuggestions
        query="/"
        isVisible={true}
        onSelect={onSelect}
      />
    );

    // Wait for the fetch to complete
    await vi.waitFor(() => {
      expect(screen.getByText("/pr_update")).toBeInTheDocument();
    });

    // Rerender with a filtered query
    rerender(
      <MicroagentSuggestions
        query="/pr"
        isVisible={true}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText("/pr_update")).toBeInTheDocument();
    expect(screen.getByText("/pr_comment")).toBeInTheDocument();
    expect(screen.queryByText("/update_test")).not.toBeInTheDocument();
  });

  it("should call onSelect when a microagent is clicked", async () => {
    const onSelect = vi.fn();

    render(
      <MicroagentSuggestions
        query="/"
        isVisible={true}
        onSelect={onSelect}
      />
    );

    // Wait for the fetch to complete
    await vi.waitFor(() => {
      expect(screen.getByText("/pr_update")).toBeInTheDocument();
    });

    // Click on a microagent
    fireEvent.click(screen.getByText("/pr_update"));

    expect(onSelect).toHaveBeenCalledWith("/pr_update");
  });

  it("should not render when isVisible is false", () => {
    const onSelect = vi.fn();

    render(
      <MicroagentSuggestions
        query="/"
        isVisible={false}
        onSelect={onSelect}
      />
    );

    expect(screen.queryByText("Loading microagents...")).not.toBeInTheDocument();
  });
});
