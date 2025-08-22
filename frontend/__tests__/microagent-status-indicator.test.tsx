import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MicroagentStatusIndicator } from "#/components/features/chat/microagent/microagent-status-indicator";
import { MicroagentStatus } from "#/types/microagent-status";

// Mock the translation hook
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("MicroagentStatusIndicator", () => {
  it("should show 'View your PR' when status is completed and PR URL is provided", () => {
    render(
      <MicroagentStatusIndicator
        status={MicroagentStatus.COMPLETED}
        conversationId="test-conversation"
        prUrl="https://github.com/owner/repo/pull/123"
      />,
    );

    const link = screen.getByRole("link", { name: "MICROAGENT$VIEW_YOUR_PR" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute(
      "href",
      "https://github.com/owner/repo/pull/123",
    );
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("should show default completed message when status is completed but no PR URL", () => {
    render(
      <MicroagentStatusIndicator
        status={MicroagentStatus.COMPLETED}
        conversationId="test-conversation"
      />,
    );

    const link = screen.getByRole("link", {
      name: "MICROAGENT$STATUS_COMPLETED",
    });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/conversations/test-conversation");
  });

  it("should show creating status without PR URL", () => {
    render(
      <MicroagentStatusIndicator
        status={MicroagentStatus.CREATING}
        conversationId="test-conversation"
      />,
    );

    expect(screen.getByText("MICROAGENT$STATUS_CREATING")).toBeInTheDocument();
  });

  it("should show error status", () => {
    render(
      <MicroagentStatusIndicator
        status={MicroagentStatus.ERROR}
        conversationId="test-conversation"
      />,
    );

    expect(screen.getByText("MICROAGENT$STATUS_ERROR")).toBeInTheDocument();
  });

  it("should prioritize PR URL over conversation link when both are provided", () => {
    render(
      <MicroagentStatusIndicator
        status={MicroagentStatus.COMPLETED}
        conversationId="test-conversation"
        prUrl="https://github.com/owner/repo/pull/123"
      />,
    );

    const link = screen.getByRole("link", { name: "MICROAGENT$VIEW_YOUR_PR" });
    expect(link).toHaveAttribute(
      "href",
      "https://github.com/owner/repo/pull/123",
    );
    // Should not link to conversation when PR URL is available
    expect(link).not.toHaveAttribute(
      "href",
      "/conversations/test-conversation",
    );
  });

  it("should work with GitLab MR URLs", () => {
    render(
      <MicroagentStatusIndicator
        status={MicroagentStatus.COMPLETED}
        prUrl="https://gitlab.com/owner/repo/-/merge_requests/456"
      />,
    );

    const link = screen.getByRole("link", { name: "MICROAGENT$VIEW_YOUR_PR" });
    expect(link).toHaveAttribute(
      "href",
      "https://gitlab.com/owner/repo/-/merge_requests/456",
    );
  });
});
