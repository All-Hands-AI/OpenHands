import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { CyberMonitor } from "#/components/features/cyber-monitor/cyber-monitor";
import { useCyberMonitorStore } from "#/stores/cyber-monitor-store";

vi.mock("#/hooks/use-tracking", () => ({
  useTracking: () => ({ trackCyberMonitorAction: vi.fn() }),
}));

describe("CyberMonitor", () => {
  beforeEach(() => {
    useCyberMonitorStore.getState().reset();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  it("renders KPIs, feed rows and console", () => {
    renderWithProviders(<CyberMonitor />);
    expect(screen.getByTestId("cyber-monitor")).toBeInTheDocument();
    expect(screen.getByTestId("cyber-kpi-blocked")).toBeInTheDocument();
    expect(screen.getAllByTestId("cyber-feed-row").length).toBeGreaterThan(0);
    expect(screen.getByTestId("cyber-console")).toBeInTheDocument();
    expect(screen.getByTestId("cyber-top-vectors")).toBeInTheDocument();
    expect(screen.getByTestId("cyber-top-ips")).toBeInTheDocument();
  });

  it("search with no match shows empty state", () => {
    renderWithProviders(<CyberMonitor />);
    fireEvent.change(screen.getByTestId("cyber-search"), {
      target: { value: "zzz-no-match-zzz" },
    });
    expect(screen.getByTestId("cyber-no-results")).toBeInTheDocument();
  });

  it("opens drawer on row click and blocks the IP", () => {
    renderWithProviders(<CyberMonitor />);
    const row = screen.getAllByTestId("cyber-feed-row")[0];
    if (!row) throw new Error("expected a feed row");
    fireEvent.click(row);
    expect(screen.getByTestId("cyber-threat-drawer")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("cyber-block-ip"));
    expect(useCyberMonitorStore.getState().blockedIps.length).toBe(1);
    expect(screen.getByTestId("cyber-block-ip")).toBeDisabled();
  });

  it("pause toggle flips store state", () => {
    renderWithProviders(<CyberMonitor />);
    fireEvent.click(screen.getByTestId("cyber-pause-toggle"));
    expect(useCyberMonitorStore.getState().isPaused).toBe(true);
  });
});
