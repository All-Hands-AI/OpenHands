import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { TrajectoryActions } from "#/components/features/trajectory/trajectory-actions";

describe("TrajectoryActions", () => {
  const user = userEvent.setup();
  const onPositiveFeedback = vi.fn();
  const onNegativeFeedback = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render correctly", () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
      />,
    );

    const actions = screen.getByTestId("feedback-actions");
    within(actions).getByTestId("positive-feedback");
    within(actions).getByTestId("negative-feedback");
  });

  it("should call onPositiveFeedback when positive feedback is clicked", async () => {
    renderWithProviders(
      <TrajectoryActions
        onPositiveFeedback={onPositiveFeedback}
        onNegativeFeedback={onNegativeFeedback}
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
      />,
    );

    const negativeFeedback = screen.getByTestId("negative-feedback");
    await user.click(negativeFeedback);

    expect(onNegativeFeedback).toHaveBeenCalled();
  });

  describe("SaaS mode", () => {
    it("should render all buttons when isSaasMode is false", () => {
      renderWithProviders(
        <TrajectoryActions
          onPositiveFeedback={onPositiveFeedback}
          onNegativeFeedback={onNegativeFeedback}
          isSaasMode={false}
        />,
      );

      const actions = screen.getByTestId("feedback-actions");
      within(actions).getByTestId("positive-feedback");
      within(actions).getByTestId("negative-feedback");
    });

    it("should render all buttons when isSaasMode is undefined (default behavior)", () => {
      renderWithProviders(
        <TrajectoryActions
          onPositiveFeedback={onPositiveFeedback}
          onNegativeFeedback={onNegativeFeedback}
        />,
      );

      const actions = screen.getByTestId("feedback-actions");
      within(actions).getByTestId("positive-feedback");
      within(actions).getByTestId("negative-feedback");
    });
  });
});
