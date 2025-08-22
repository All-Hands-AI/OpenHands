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

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render correctly", () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
        onExportTrajectory={onExportTrajectory}
      />,
    );

    const actions = screen.getByTestId("feedback-actions");
    within(actions).getByTestId("positive-feedback");
    within(actions).getByTestId("negative-feedback");
    within(actions).getByTestId("export-trajectory");
  });

  it("should call onPositiveFeedback when positive feedback is clicked", async () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
        onExportTrajectory={onExportTrajectory}
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
      />,
    );

    const exportButton = screen.getByTestId("export-trajectory");
    await user.click(exportButton);

    expect(onExportTrajectory).toHaveBeenCalled();
  });

  describe("SaaS mode", () => {
    it("should only render export button when isSaasMode is true", () => {
      renderWithProviders(
        <TrajectoryActions
          onPositiveFeedback={onPositiveFeedback}
          onNegativeFeedback={onNegativeFeedback}
          onExportTrajectory={onExportTrajectory}
          isSaasMode={true}
        />,
      );

      const actions = screen.getByTestId("feedback-actions");

      // Should not render feedback buttons in SaaS mode
      expect(within(actions).queryByTestId("positive-feedback")).toBeNull();
      expect(within(actions).queryByTestId("negative-feedback")).toBeNull();

      // Should still render export button
      within(actions).getByTestId("export-trajectory");
    });

    it("should render all buttons when isSaasMode is false", () => {
      renderWithProviders(
        <TrajectoryActions
          onPositiveFeedback={onPositiveFeedback}
          onNegativeFeedback={onNegativeFeedback}
          onExportTrajectory={onExportTrajectory}
          isSaasMode={false}
        />,
      );

      const actions = screen.getByTestId("feedback-actions");
      within(actions).getByTestId("positive-feedback");
      within(actions).getByTestId("negative-feedback");
      within(actions).getByTestId("export-trajectory");
    });

    it("should render all buttons when isSaasMode is undefined (default behavior)", () => {
      renderWithProviders(
        <TrajectoryActions
          onPositiveFeedback={onPositiveFeedback}
          onNegativeFeedback={onNegativeFeedback}
          onExportTrajectory={onExportTrajectory}
        />,
      );

      const actions = screen.getByTestId("feedback-actions");
      within(actions).getByTestId("positive-feedback");
      within(actions).getByTestId("negative-feedback");
      within(actions).getByTestId("export-trajectory");
    });

    it("should call onExportTrajectory when export button is clicked in SaaS mode", async () => {
      renderWithProviders(
        <TrajectoryActions
          onPositiveFeedback={onPositiveFeedback}
          onNegativeFeedback={onNegativeFeedback}
          onExportTrajectory={onExportTrajectory}
          isSaasMode={true}
        />,
      );

      const exportButton = screen.getByTestId("export-trajectory");
      await user.click(exportButton);

      expect(onExportTrajectory).toHaveBeenCalled();
    });
  });
});
