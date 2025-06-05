import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LaunchMicroagentModal } from "#/components/features/chat/microagent/launch-microagent-modal";
import { MemoryService } from "#/api/memory-service/memory-service.api";
import { FileService } from "#/api/file-service/file-service.api";

vi.mock("react-router", async () => ({
  useParams: vi.fn().mockReturnValue({
    conversationId: "123",
  }),
}));

// Mock the useHandleRuntimeActive hook
vi.mock("#/hooks/use-handle-runtime-active", () => ({
  useHandleRuntimeActive: vi.fn().mockReturnValue({ runtimeActive: true }),
}));

// Mock the useMicroagentPrompt hook
vi.mock("#/hooks/query/use-microagent-prompt", () => ({
  useMicroagentPrompt: vi.fn().mockReturnValue({ 
    data: "Generated prompt", 
    isLoading: false 
  }),
}));

// Mock the useGetMicroagents hook
vi.mock("#/hooks/query/use-get-microagents", () => ({
  useGetMicroagents: vi.fn().mockReturnValue({ 
    data: ["file1", "file2"] 
  }),
}));

describe("LaunchMicroagentModal", () => {
  const onCloseMock = vi.fn();
  const onLaunchMock = vi.fn();
  const eventId = 12;
  const conversationId = "123";

  const renderMicroagentModal = (
    { isLoading }: { isLoading: boolean } = { isLoading: false },
  ) =>
    render(
      <LaunchMicroagentModal
        onClose={onCloseMock}
        onLaunch={onLaunchMock}
        eventId={eventId}
        selectedRepo="some-repo"
        isLoading={isLoading}
      />,
      {
        wrapper: ({ children }) => (
          <QueryClientProvider client={new QueryClient()}>
            {children}
          </QueryClientProvider>
        ),
      },
    );

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the launch microagent modal", () => {
    renderMicroagentModal();
    expect(screen.getByTestId("launch-microagent-modal")).toBeInTheDocument();
  });

  it("should render the form fields", () => {
    renderMicroagentModal();

    // inputs
    screen.getByTestId("query-input");
    screen.getByTestId("target-input");
    screen.getByTestId("trigger-input");

    // action buttons
    screen.getByRole("button", { name: "Launch" });
    screen.getByRole("button", { name: "Cancel" });
  });

  it("should call onClose when pressing the cancel button", async () => {
    renderMicroagentModal();

    const cancelButton = screen.getByRole("button", { name: "Cancel" });
    await userEvent.click(cancelButton);
    expect(onCloseMock).toHaveBeenCalled();
  });

  it("should display the prompt from the hook", async () => {
    renderMicroagentModal();
    
    // Since we're mocking the hook, we just need to verify the UI shows the data
    const descriptionInput = screen.getByTestId("query-input");
    expect(descriptionInput).toHaveValue("Generated prompt");
  });

  it("should display the list of microagent files from the hook", async () => {
    renderMicroagentModal();
    
    // Since we're mocking the hook, we just need to verify the UI shows the data
    const targetInput = screen.getByTestId("target-input");
    expect(targetInput).toHaveValue("");

    await userEvent.click(targetInput);

    expect(screen.getByText("file1")).toBeInTheDocument();
    expect(screen.getByText("file2")).toBeInTheDocument();

    await userEvent.click(screen.getByText("file1"));
    expect(targetInput).toHaveValue("file1");
  });

  it("should call onLaunch with the form data", async () => {
    renderMicroagentModal();

    const triggerInput = screen.getByTestId("trigger-input");
    await userEvent.type(triggerInput, "trigger1 ");
    await userEvent.type(triggerInput, "trigger2 ");

    const targetInput = screen.getByTestId("target-input");
    await userEvent.click(targetInput);
    await userEvent.click(screen.getByText("file1"));

    const launchButton = await screen.findByRole("button", { name: "Launch" });
    await userEvent.click(launchButton);

    expect(onLaunchMock).toHaveBeenCalledWith("Generated prompt", "file1", [
      "trigger1",
      "trigger2",
    ]);
  });

  it("should disable the launch button if isLoading is true", async () => {
    renderMicroagentModal({ isLoading: true });

    const launchButton = screen.getByRole("button", { name: "Launch" });
    expect(launchButton).toBeDisabled();
  });
});
