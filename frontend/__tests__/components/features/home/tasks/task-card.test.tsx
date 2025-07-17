import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskCard } from "#/components/features/home/tasks/task-card";
import { SuggestedTask } from "#/components/features/home/tasks/task.types";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the hooks
vi.mock("#/hooks/mutation/use-create-conversation", () => ({
  useCreateConversation: vi.fn(),
}));

vi.mock("#/hooks/use-is-creating-conversation", () => ({
  useIsCreatingConversation: vi.fn(),
}));

vi.mock("#/hooks/use-optimistic-user-message", () => ({
  useOptimisticUserMessage: vi.fn(),
}));

// Mock react-router with a global mock
const mockNavigate = vi.fn();
vi.mock("react-router", () => ({
  useNavigate: () => mockNavigate,
}));

// Mock i18n
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("TaskCard", () => {
  const mockTask: SuggestedTask = {
    issue_number: 123,
    title: "Fix bug",
    repo: "test/repo",
    git_provider: "github",
    task_type: "OPEN_ISSUE",
  };

  const mockCreateConversation = vi.fn();
  const mockSetOptimisticUserMessage = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    (useCreateConversation as jest.Mock).mockReturnValue({
      mutate: mockCreateConversation,
      isPending: false,
    });
    
    (useIsCreatingConversation as jest.Mock).mockReturnValue(false);
    
    (useOptimisticUserMessage as jest.Mock).mockReturnValue({
      setOptimisticUserMessage: mockSetOptimisticUserMessage,
    });
  });

  it("should create a conversation when Launch button is clicked", async () => {
    render(<TaskCard task={mockTask} />);
    
    const launchButton = screen.getByTestId("task-launch-button");
    await userEvent.click(launchButton);
    
    expect(mockSetOptimisticUserMessage).toHaveBeenCalledWith("TASK$ADDRESSING_TASK");
    expect(mockCreateConversation).toHaveBeenCalledWith({
      repository: {
        name: mockTask.repo,
        gitProvider: mockTask.git_provider,
      },
      suggestedTask: mockTask,
    });
  });

  it("should navigate to the conversation page after creating a conversation", async () => {
    // Reset mocks before test
    vi.clearAllMocks();
    
    // Mock successful conversation creation with proper callback handling
    mockCreateConversation.mockImplementation((params, options) => {
      if (options && options.onSuccess) {
        options.onSuccess({ conversation_id: "test-conversation-id" });
      }
    });

    render(<TaskCard task={mockTask} />);
    
    const launchButton = screen.getByTestId("task-launch-button");
    await userEvent.click(launchButton);
    
    // This test should pass now that we've implemented navigation
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/conversations/test-conversation-id");
    });
  });
});