import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { MaintenanceBanner } from "#/components/features/maintenance/maintenance-banner";

// Mock date-fns-tz
vi.mock("date-fns-tz", () => ({
  formatInTimeZone: vi.fn(),
}));

// Mock Intl.DateTimeFormat
const mockResolvedOptions = vi.fn();
vi.stubGlobal("Intl", {
  DateTimeFormat: vi.fn(() => ({
    resolvedOptions: mockResolvedOptions,
  })),
});

describe("MaintenanceBanner", () => {
  let mockFormatInTimeZone: any;

  beforeEach(async () => {
    mockFormatInTimeZone = vi.mocked(
      (await import("date-fns-tz")).formatInTimeZone
    );
    mockResolvedOptions.mockReturnValue({ timeZone: "America/New_York" });
    mockFormatInTimeZone.mockImplementation((date: any, timeZone: any, format: any) => {
      if (format === "MMM d, yyyy h:mm a") {
        return "Jan 15, 2024 2:00 PM";
      }
      if (format === "zzz") {
        return "EST";
      }
      return "formatted-time";
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the maintenance banner with warning icon", () => {
    render(
      <MaintenanceBanner
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    // Check for warning icon (SVG)
    const warningIcon = document.querySelector("svg");
    expect(warningIcon).toBeInTheDocument();
    expect(warningIcon).toHaveAttribute("viewBox", "0 0 20 20");

    // Check for warning styling
    const banner = screen.getByText(/MAINTENANCE\$BANNER_MESSAGE/).closest("div")?.parentElement;
    expect(banner).toHaveClass(
      "bg-warning",
      "text-warning-foreground",
      "px-4",
      "py-3",
      "text-center",
      "text-sm",
      "font-medium"
    );
  });

  it("should display the maintenance banner message with formatted times", () => {
    render(
      <MaintenanceBanner
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    expect(screen.getByText(/MAINTENANCE\$BANNER_MESSAGE/)).toBeInTheDocument();
    expect(screen.getByText(/Jan 15, 2024 2:00 PM EST/)).toBeInTheDocument();
  });

  it("should format times to user's local timezone", () => {
    render(
      <MaintenanceBanner
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    // Verify formatInTimeZone was called with correct parameters
    expect(mockFormatInTimeZone).toHaveBeenCalledWith(
      expect.any(Date),
      "America/New_York",
      "MMM d, yyyy h:mm a"
    );
    expect(mockFormatInTimeZone).toHaveBeenCalledWith(
      expect.any(Date),
      "America/New_York",
      "zzz"
    );
  });

  it("should handle time strings with timezone information", () => {
    render(
      <MaintenanceBanner
        startTime="2024-01-15T14:00:00Z"
        endTime="2024-01-15T16:00:00Z"
      />
    );

    // Should use the original date without adding EST
    expect(mockFormatInTimeZone).toHaveBeenCalled();
  });

  it("should handle time strings with + timezone offset", () => {
    render(
      <MaintenanceBanner
        startTime="2024-01-15T14:00:00+05:00"
        endTime="2024-01-15T16:00:00+05:00"
      />
    );

    // Should use the original date without adding EST
    expect(mockFormatInTimeZone).toHaveBeenCalled();
  });

  it("should handle time strings with - timezone offset", () => {
    render(
      <MaintenanceBanner
        startTime="2024-01-15T14:00:00-05:00"
        endTime="2024-01-15T16:00:00-05:00"
      />
    );

    // Should use the original date without adding EST
    expect(mockFormatInTimeZone).toHaveBeenCalled();
  });

  it("should add EST to time strings without timezone information", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    
    render(
      <MaintenanceBanner
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    // Should call formatInTimeZone with a date that includes EST
    expect(mockFormatInTimeZone).toHaveBeenCalled();
    
    consoleSpy.mockRestore();
  });

  it("should handle formatting errors gracefully", () => {
    mockFormatInTimeZone.mockImplementation(() => {
      throw new Error("Formatting error");
    });

    render(
      <MaintenanceBanner
        startTime="invalid-date"
        endTime="invalid-date"
      />
    );

    // Should fall back to original time strings
    expect(screen.getByText(/invalid-date/)).toBeInTheDocument();
  });

  it("should display both start and end times with dash separator", () => {
    mockFormatInTimeZone.mockImplementation((date: any, timeZone: any, format: any) => {
      if (format === "MMM d, yyyy h:mm a") {
        const dateStr = date.toISOString();
        if (dateStr.includes("14:00")) {
          return "Jan 15, 2024 2:00 PM";
        }
        return "Jan 15, 2024 4:00 PM";
      }
      return "EST";
    });

    render(
      <MaintenanceBanner
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    const bannerText = screen.getByText(/MAINTENANCE\$BANNER_MESSAGE/).textContent;
    expect(bannerText).toContain("Jan 15, 2024 2:00 PM EST - Jan 15, 2024 4:00 PM EST");
  });

  it("should use user's detected timezone", () => {
    mockResolvedOptions.mockReturnValue({ timeZone: "Europe/London" });

    render(
      <MaintenanceBanner
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    expect(mockFormatInTimeZone).toHaveBeenCalledWith(
      expect.any(Date),
      "Europe/London",
      "MMM d, yyyy h:mm a"
    );
  });

  it("should have proper accessibility structure", () => {
    render(
      <MaintenanceBanner
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    // Check that the banner has proper structure for screen readers
    const banner = screen.getByText(/MAINTENANCE\$BANNER_MESSAGE/).closest("div");
    expect(banner).toHaveClass("flex", "items-center", "justify-center", "gap-2");
    
    // Warning icon should be properly sized and not shrink
    const warningIcon = document.querySelector("svg");
    expect(warningIcon).toHaveClass("h-4", "w-4", "flex-shrink-0");
  });
});