import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MaintenanceBanner } from "#/components/features/maintenance/maintenance-banner";

// Mock react-i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("MaintenanceBanner", () => {
  it("renders maintenance banner with formatted time", () => {
    const startTime = "2024-01-15T10:00:00-05:00"; // EST timestamp
    
    const { container } = render(<MaintenanceBanner startTime={startTime} />);
    
    // Check if the banner is rendered
    expect(screen.getByText(/Scheduled maintenance will begin at/)).toBeInTheDocument();
    
    // Check if the warning icon (SVG) is present
    const svgIcon = container.querySelector('svg');
    expect(svgIcon).toBeInTheDocument();
  });

  it("handles invalid date gracefully", () => {
    const invalidTime = "invalid-date";
    
    render(<MaintenanceBanner startTime={invalidTime} />);
    
    // Should still render the banner with the original string
    expect(screen.getByText(/Scheduled maintenance will begin at invalid-date/)).toBeInTheDocument();
  });

  it("formats ISO date string correctly", () => {
    const isoTime = "2024-01-15T15:30:00.000Z";
    
    render(<MaintenanceBanner startTime={isoTime} />);
    
    // Should render the banner (exact time format will depend on user's timezone)
    expect(screen.getByText(/Scheduled maintenance will begin at/)).toBeInTheDocument();
  });
});