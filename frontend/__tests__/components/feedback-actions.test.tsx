import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { TrajectoryActions } from "#/components/features/trajectory/trajectory-actions";

describe("TrajectoryActions", () => {
  const user = userEvent.setup();
  const onPositiveFeedback = vi.fn();
  const onNegativeFeedback = vi.fn();
  const onExportTrajectory = vi.fn();
  const onSummarizeConversation = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render correctly", () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
        onExportTrajectory={onExportTrajectory}
        onSummarizeConversation={onSummarizeConversation}
      />,
    );

    const actions = screen.getByTestId("feedback-actions");
    within(actions).getByTestId("positive-feedback");
    within(actions).getByTestId("negative-feedback");
    within(actions).getByTestId("export-trajectory");
    within(actions).getByTestId("summarize-conversation");
  });

  it("should call onPositiveFeedback when positive feedback is clicked", async () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
        onExportTrajectory={onExportTrajectory}
        onSummarizeConversation={onSummarizeConversation}
      />,
    );

    const positiveFeedback = screen.getByTestId("positive-feedback");
    await user.click(positiveFeedback);

    expect(onPositiveFeedback).toHaveBeenCalled();
  });

  it("should call onNegativeFeedback when negative feedback is clicked", async () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
        onExportTrajectory={onExportTrajectory}
        onSummarizeConversation={onSummarizeConversation}
      />,
    );

    const negativeFeedback = screen.getByTestId("negative-feedback");
    await user.click(negativeFeedback);

    expect(onNegativeFeedback).toHaveBeenCalled();
  });

  it("should call onExportTrajectory when export button is clicked", async () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
        onExportTrajectory={onExportTrajectory}
        onSummarizeConversation={onSummarizeConversation}
      />,
    );

    const exportButton = screen.getByTestId("export-trajectory");
    await user.click(exportButton);

    expect(onExportTrajectory).toHaveBeenCalled();
  });

  it("should call onSummarizeConversation when summarize button is clicked", async () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
        onExportTrajectory={onExportTrajectory}
        onSummarizeConversation={onSummarizeConversation}
      />,
    );

    const summarizeButton = screen.getByTestId("summarize-conversation");
    await user.click(summarizeButton);

    expect(onSummarizeConversation).toHaveBeenCalled();
  });
});
