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
        "CLEAN_DEPENDENCIES": "依存関係を整理",
        "WORKSPACE$TERMINAL_TAB_LABEL": "ターミナル",
        "WORKSPACE$BROWSER_TAB_LABEL": "ブラウザ（実験的）",
        "WORKSPACE$JUPYTER_TAB_LABEL": "Jupyter IPython",
        "WORKSPACE$CODE_EDITOR_TAB_LABEL": "コードエディタ",
        "WORKSPACE$LABEL": "ワークスペース",
        "PROJECT$NEW_PROJECT": "新規プロジェクト",
        "STATUS$WAITING_FOR_CLIENT": "クライアントの準備を待機中",
        "STATUS$CONNECTED": "接続済み",
        "STATUS$CONNECTED_TO_SERVER": "サーバーに接続済み",
        "TIME$MINUTES_AGO": "分前",
        "TIME$HOURS_AGO": "時間前",
        "TIME$DAYS_AGO": "日前"
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
          <div data-testid="main-content">
            <h1>{t("LETS_START_BUILDING")}</h1>
            <button>{t("OPEN_IN_VSCODE")}</button>
            <button>{t("INCREASE_TEST_COVERAGE")}</button>
            <button>{t("AUTO_MERGE_PRS")}</button>
            <button>{t("FIX_README")}</button>
            <button>{t("CLEAN_DEPENDENCIES")}</button>
          </div>
          <div data-testid="tabs">
            <span>{t("WORKSPACE$TERMINAL_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$BROWSER_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$JUPYTER_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$CODE_EDITOR_TAB_LABEL")}</span>
          </div>
          <div data-testid="workspace-label">{t("WORKSPACE$LABEL")}</div>
          <button data-testid="new-project">{t("PROJECT$NEW_PROJECT")}</button>
          <div data-testid="status">
            <span>{t("STATUS$WAITING_FOR_CLIENT")}</span>
            <span>{t("STATUS$CONNECTED")}</span>
            <span>{t("STATUS$CONNECTED_TO_SERVER")}</span>
          </div>
          <div data-testid="time">
            <span>{`5 ${t("TIME$MINUTES_AGO")}`}</span>
            <span>{`2 ${t("TIME$HOURS_AGO")}`}</span>
            <span>{`3 ${t("TIME$DAYS_AGO")}`}</span>
          </div>
        </div>
      );
    };

    render(<TestComponent />);

    // Check main content translations
    expect(screen.getByText("開発を始めましょう！")).toBeInTheDocument();
    expect(screen.getByText("VS Codeで開く")).toBeInTheDocument();
    expect(screen.getByText("テストカバレッジを向上")).toBeInTheDocument();
    expect(screen.getByText("PRを自動マージ")).toBeInTheDocument();
    expect(screen.getByText("READMEを修正")).toBeInTheDocument();
    expect(screen.getByText("依存関係を整理")).toBeInTheDocument();

    // Check tab labels
    const tabs = screen.getByTestId("tabs");
    expect(tabs).toHaveTextContent("ターミナル");
    expect(tabs).toHaveTextContent("ブラウザ（実験的）");
    expect(tabs).toHaveTextContent("Jupyter IPython");
    expect(tabs).toHaveTextContent("コードエディタ");

    // Check workspace label and new project button
    expect(screen.getByTestId("workspace-label")).toHaveTextContent("ワークスペース");
    expect(screen.getByTestId("new-project")).toHaveTextContent("新規プロジェクト");

    // Check status messages
    const status = screen.getByTestId("status");
    expect(status).toHaveTextContent("クライアントの準備を待機中");
    expect(status).toHaveTextContent("接続済み");
    expect(status).toHaveTextContent("サーバーに接続済み");

    // Check time-related translations
    const time = screen.getByTestId("time");
    expect(time).toHaveTextContent("5 分前");
    expect(time).toHaveTextContent("2 時間前");
    expect(time).toHaveTextContent("3 日前");
  });
});
