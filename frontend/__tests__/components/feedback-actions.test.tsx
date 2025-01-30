import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { TrajectoryActions } from "#/components/features/trajectory/trajectory-actions";
import { SettingsProvider } from "#/context/settings-context";
import { AuthProvider } from "#/context/auth-context";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

describe("TrajectoryActions", () => {
  const user = userEvent.setup();
  const onPositiveFeedback = vi.fn();
  const onNegativeFeedback = vi.fn();
  const onExportTrajectory = vi.fn();
  const queryClient = new QueryClient();

  const renderWithProviders = (children: React.ReactNode) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <SettingsProvider>{children}</SettingsProvider>
        </AuthProvider>
      </QueryClientProvider>
    );
  };

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
    within(actions).getByTestId("sound-toggle");
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
});