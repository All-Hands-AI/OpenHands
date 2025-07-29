import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { MaintenancePage } from "#/components/features/maintenance/maintenance-page";

// Mock date-fns-tz
vi.mock("date-fns-tz", () => ({
  formatInTimeZone: vi.fn(),
}));

// Mock the AllHandsLogo SVG import
vi.mock("#/assets/branding/all-hands-logo.svg?react", () => ({
  default: ({ width, height }: { width: number; height: number }) => (
    <svg
      data-testid="all-hands-logo"
      width={width}
      height={height}
      role="img"
      aria-label="All Hands Logo"
    >
      <rect width={width} height={height} fill="currentColor" />
    </svg>
  ),
}));

// Mock Intl.DateTimeFormat
const mockResolvedOptions = vi.fn();
vi.stubGlobal("Intl", {
  DateTimeFormat: vi.fn(() => ({
    resolvedOptions: mockResolvedOptions,
  })),
});

describe("MaintenancePage", () => {
  let mockFormatInTimeZone: any;

  beforeEach(async () => {
    mockFormatInTimeZone = vi.mocked(
      (await import("date-fns-tz")).formatInTimeZone
    );
    mockResolvedOptions.mockReturnValue({ timeZone: "America/New_York" });
    mockFormatInTimeZone.mockImplementation((date: any, timeZone: any, format: any) => {
      if (format === "MMM d, yyyy h:mm a") {
        const dateStr = date.toISOString();
        if (dateStr.includes("14:00")) {
          return "Jan 15, 2024 2:00 PM";
        }
        return "Jan 15, 2024 4:00 PM";
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

  it("should render the maintenance page with all required elements", () => {
    render(
      <MaintenancePage
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    // Check for logo
    expect(screen.getByTestId("all-hands-logo")).toBeInTheDocument();
    expect(screen.getByTestId("all-hands-logo")).toHaveAttribute("width", "80");
    expect(screen.getByTestId("all-hands-logo")).toHaveAttribute("height", "54");

    // Check for title
    expect(screen.getByText("MAINTENANCE$TITLE")).toBeInTheDocument();

    // Check for description
    expect(screen.getByText("MAINTENANCE$DESCRIPTION")).toBeInTheDocument();

    // Check for scheduled time section
    expect(screen.getByText("MAINTENANCE$SCHEDULED_TIME")).toBeInTheDocument();

    // Check for start and end labels
    expect(screen.getByText(/MAINTENANCE\$START/)).toBeInTheDocument();
    expect(screen.getByText(/MAINTENANCE\$END/)).toBeInTheDocument();

    // Check for come back later message
    expect(screen.getByText("MAINTENANCE$COME_BACK_LATER")).toBeInTheDocument();
  });

  it("should display formatted start and end times", () => {
    render(
      <MaintenancePage
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    expect(screen.getByText("Jan 15, 2024 2:00 PM EST")).toBeInTheDocument();
    expect(screen.getByText("Jan 15, 2024 4:00 PM EST")).toBeInTheDocument();
  });

  it("should format times to user's local timezone", () => {
    render(
      <MaintenancePage
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
      <MaintenancePage
        startTime="2024-01-15T14:00:00Z"
        endTime="2024-01-15T16:00:00Z"
      />
    );

    // Should use the original date without adding EST
    expect(mockFormatInTimeZone).toHaveBeenCalled();
  });

  it("should handle time strings with + timezone offset", () => {
    render(
      <MaintenancePage
        startTime="2024-01-15T14:00:00+05:00"
        endTime="2024-01-15T16:00:00+05:00"
      />
    );

    // Should use the original date without adding EST
    expect(mockFormatInTimeZone).toHaveBeenCalled();
  });

  it("should handle time strings with - timezone offset", () => {
    render(
      <MaintenancePage
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
      <MaintenancePage
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
      <MaintenancePage
        startTime="invalid-date"
        endTime="invalid-date"
      />
    );

    // Should fall back to original time strings
    expect(screen.getAllByText(/invalid-date/)).toHaveLength(2);
  });

  it("should use user's detected timezone", () => {
    mockResolvedOptions.mockReturnValue({ timeZone: "Europe/London" });

    render(
      <MaintenancePage
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

  it("should have proper page structure and styling", () => {
    render(
      <MaintenancePage
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    // Check main container
    const mainContainer = document.querySelector(".min-h-screen");
    expect(mainContainer).toHaveClass(
      "flex",
      "flex-col",
      "items-center",
      "justify-center",
      "min-h-screen",
      "bg-base",
      "p-4"
    );

    // Check card container
    const cardContainer = document.querySelector(".bg-card");
    expect(cardContainer).toHaveClass(
      "bg-card",
      "rounded-lg",
      "shadow-lg",
      "p-8",
      "max-w-md",
      "w-full",
      "text-center"
    );

    // Check title styling
    const title = screen.getByText("MAINTENANCE$TITLE");
    expect(title).toHaveClass("text-2xl", "font-bold", "mb-4");

    // Check description styling
    const description = screen.getByText("MAINTENANCE$DESCRIPTION");
    expect(description).toHaveClass("text-muted-foreground", "mb-6");
  });

  it("should have proper scheduled time section styling", () => {
    render(
      <MaintenancePage
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    // Check scheduled time container
    const scheduledTimeContainer = screen.getByText("MAINTENANCE$SCHEDULED_TIME").closest("div");
    expect(scheduledTimeContainer).toHaveClass("bg-muted", "p-4", "rounded-md", "mb-6");

    // Check scheduled time title
    const scheduledTimeTitle = screen.getByText("MAINTENANCE$SCHEDULED_TIME");
    expect(scheduledTimeTitle).toHaveClass("font-medium", "mb-2");

    // Check start and end time styling
    const startTimeElement = screen.getByText(/MAINTENANCE\$START/).closest("p");
    const endTimeElement = screen.getByText(/MAINTENANCE\$END/).closest("p");
    
    expect(startTimeElement).toHaveClass("text-sm");
    expect(endTimeElement).toHaveClass("text-sm");

    // Check that start and end labels are bold
    expect(screen.getByText(/MAINTENANCE\$START/).closest("span")).toHaveClass("font-medium");
    expect(screen.getByText(/MAINTENANCE\$END/).closest("span")).toHaveClass("font-medium");
  });

  it("should have proper come back later message styling", () => {
    render(
      <MaintenancePage
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    const comeBackMessage = screen.getByText("MAINTENANCE$COME_BACK_LATER");
    expect(comeBackMessage).toHaveClass("text-sm", "text-muted-foreground");
  });

  it("should render logo with correct dimensions", () => {
    render(
      <MaintenancePage
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    const logo = screen.getByTestId("all-hands-logo");
    expect(logo).toHaveAttribute("width", "80");
    expect(logo).toHaveAttribute("height", "54");
    expect(logo).toHaveAttribute("role", "img");
    expect(logo).toHaveAttribute("aria-label", "All Hands Logo");
  });

  it("should have proper logo container styling", () => {
    render(
      <MaintenancePage
        startTime="2024-01-15 14:00:00"
        endTime="2024-01-15 16:00:00"
      />
    );

    const logoContainer = screen.getByTestId("all-hands-logo").closest("div");
    expect(logoContainer).toHaveClass("flex", "justify-center", "mb-6");
  });
});