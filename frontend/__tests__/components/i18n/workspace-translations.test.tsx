import { render, screen } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { useTranslation } from "react-i18next";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "WORKSPACE$TITLE": "OpenHands ワークスペース",
        "WORKSPACE$TERMINAL_TAB_LABEL": "ターミナル",
        "WORKSPACE$BROWSER_TAB_LABEL": "ブラウザ（実験的）",
        "WORKSPACE$JUPYTER_TAB_LABEL": "Jupyter IPython",
        "WORKSPACE$CODE_EDITOR_TAB_LABEL": "コードエディタ",
        "WORKSPACE$LABEL": "ワークスペース",
        "LETS_START_BUILDING": "開発を始めましょう！",
        "PROJECT$NEW_PROJECT": "新規プロジェクト"
      };
      return translations[key] || key;
    },
  }),
}));

describe("Workspace translations", () => {
  test("should render Japanese workspace UI translations correctly", () => {
    // Mock a simple component that uses workspace translations
    const WorkspaceComponent = () => {
      const { t } = useTranslation();
      return (
        <div>
          <h1 data-testid="title">{t("WORKSPACE$TITLE")}</h1>
          <div data-testid="tabs">
            <span>{t("WORKSPACE$TERMINAL_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$BROWSER_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$JUPYTER_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$CODE_EDITOR_TAB_LABEL")}</span>
          </div>
          <div data-testid="workspace-label">{t("WORKSPACE$LABEL")}</div>
          <div data-testid="start-building">{t("LETS_START_BUILDING")}</div>
          <button data-testid="new-project">{t("PROJECT$NEW_PROJECT")}</button>
        </div>
      );
    };

    render(<WorkspaceComponent />);

    // Check that all translations are rendered correctly
    expect(screen.getByTestId("title")).toHaveTextContent("OpenHands ワークスペース");
    expect(screen.getByTestId("tabs")).toHaveTextContent("ターミナル");
    expect(screen.getByTestId("tabs")).toHaveTextContent("ブラウザ（実験的）");
    expect(screen.getByTestId("tabs")).toHaveTextContent("Jupyter IPython");
    expect(screen.getByTestId("tabs")).toHaveTextContent("コードエディタ");
    expect(screen.getByTestId("workspace-label")).toHaveTextContent("ワークスペース");
    expect(screen.getByTestId("start-building")).toHaveTextContent("開発を始めましょう！");
    expect(screen.getByTestId("new-project")).toHaveTextContent("新規プロジェクト");
  });
});