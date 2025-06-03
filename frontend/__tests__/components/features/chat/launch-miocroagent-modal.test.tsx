import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LaunchMicroagentModal } from "#/components/features/chat/launch-miocroagent-modal";
import { MemoryService } from "#/api/memory-service/memory-service.api";
import { FileService } from "#/api/file-service/file-service.api";

vi.mock("react-router", async () => ({
  useParams: vi.fn().mockReturnValue({
    conversationId: "123",
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
    screen.getByTestId("description-input");
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

  it("should make a query to get the prompt", async () => {
    const getPromptSpy = vi.spyOn(MemoryService, "getPrompt");
    getPromptSpy.mockResolvedValue("Generated prompt");
    renderMicroagentModal();

    expect(getPromptSpy).toHaveBeenCalledWith(conversationId, eventId);
    const descriptionInput = screen.getByTestId("description-input");
    await waitFor(() =>
      expect(descriptionInput).toHaveValue("Generated prompt"),
    );
  });

  it("should make a query to get the list of valid target files if user has a selected repo", async () => {
    const getMicroagentFiles = vi.spyOn(FileService, "getFiles");
    getMicroagentFiles.mockResolvedValue(["file1", "file2"]);
    renderMicroagentModal();

    expect(getMicroagentFiles).toHaveBeenCalledWith(
      conversationId,
      "some-repo/.openhands/microagents/",
    );

    const targetInput = screen.getByTestId("target-input");
    expect(targetInput).toHaveValue("");

    await userEvent.click(targetInput);

    expect(screen.getByText("file1")).toBeInTheDocument();
    expect(screen.getByText("file2")).toBeInTheDocument();

    await userEvent.click(screen.getByText("file1"));
    expect(targetInput).toHaveValue("file1");
  });

  it("should call onLaunch with the form data", async () => {
    const getPromptSpy = vi.spyOn(MemoryService, "getPrompt");
    const getMicroagentFiles = vi.spyOn(FileService, "getFiles");

    getPromptSpy.mockResolvedValue("Generated prompt");
    getMicroagentFiles.mockResolvedValue(["file1", "file2"]);

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
