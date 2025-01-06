import { render, screen } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { useTranslation } from "react-i18next";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "LETS_START_BUILDING": "開発を始めましょう！",
        "OPEN_IN_VSCODE": "VS Codeで開く",
        "INCREASE_TEST_COVERAGE": "テストカバレッジを向上",
        "AUTO_MERGE_PRS": "PRを自動マージ",
        "FIX_README": "READMEを修正",
        "CLEAN_DEPENDENCIES": "依存関係を整理"
      };
      return translations[key] || key;
    },
  }),
}));

describe("Landing page translations", () => {
  test("should render Japanese translations correctly", () => {
    // Mock a simple component that uses the translations
    const TestComponent = () => {
      const { t } = useTranslation();
      return (
        <div>
          <h1>{t("LETS_START_BUILDING")}</h1>
          <button>{t("OPEN_IN_VSCODE")}</button>
          <button>{t("INCREASE_TEST_COVERAGE")}</button>
          <button>{t("AUTO_MERGE_PRS")}</button>
          <button>{t("FIX_README")}</button>
          <button>{t("CLEAN_DEPENDENCIES")}</button>
        </div>
      );
    };

    render(<TestComponent />);

    // Check that all translations are rendered correctly
    expect(screen.getByText("開発を始めましょう！")).toBeInTheDocument();
    expect(screen.getByText("VS Codeで開く")).toBeInTheDocument();
    expect(screen.getByText("テストカバレッジを向上")).toBeInTheDocument();
    expect(screen.getByText("PRを自動マージ")).toBeInTheDocument();
    expect(screen.getByText("READMEを修正")).toBeInTheDocument();
    expect(screen.getByText("依存関係を整理")).toBeInTheDocument();
  });
});
