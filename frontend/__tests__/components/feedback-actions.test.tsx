import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
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
    render(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
        onExportTrajectory={onExportTrajectory}
      />,
    );

    const actions = screen.getByTestId("feedback-actions");
    within(actions).getByTestId("positive-feedback");
    within(actions).getByTestId("negative-feedback");
  });

  it("should call onPositiveFeedback when positive feedback is clicked", async () => {
    render(
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
    render(
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

  it("should call onExportTrajectory when negative feedback is clicked", async () => {
    render(
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
});
