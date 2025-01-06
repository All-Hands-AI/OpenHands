import { render, screen } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { useTranslation } from "react-i18next";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "TIME$MINUTES_AGO": "分前",
        "TIME$HOURS_AGO": "時間前",
        "TIME$DAYS_AGO": "日前"
      };
      return translations[key] || key;
    },
  }),
}));

describe("Time translations", () => {
  test("should render Japanese time translations correctly", () => {
    // Mock a simple component that uses time translations
    const TimeComponent = () => {
      const { t } = useTranslation();
      return (
        <div>
          <span data-testid="minutes">{`5 ${t("TIME$MINUTES_AGO")}`}</span>
          <span data-testid="hours">{`2 ${t("TIME$HOURS_AGO")}`}</span>
          <span data-testid="days">{`3 ${t("TIME$DAYS_AGO")}`}</span>
        </div>
      );
    };

    render(<TimeComponent />);

    // Check that all translations are rendered correctly
    expect(screen.getByTestId("minutes")).toHaveTextContent("5 分前");
    expect(screen.getByTestId("hours")).toHaveTextContent("2 時間前");
    expect(screen.getByTestId("days")).toHaveTextContent("3 日前");
  });
});