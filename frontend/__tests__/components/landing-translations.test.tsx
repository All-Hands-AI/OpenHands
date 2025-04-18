import { render, screen } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { useTranslation } from "react-i18next";
import translations from "../../src/i18n/translation.json";
import { UserAvatar } from "../../src/components/features/sidebar/user-avatar";

vi.mock("@heroui/react", () => ({
  Tooltip: ({ content, children }: { content: string; children: React.ReactNode }) => (
    <div>
      {children}
      <div>{content}</div>
    </div>
  ),
}));

const supportedLanguages = ['en', 'ja', 'zh-CN', 'zh-TW', 'ko-KR', 'de', 'no', 'it', 'pt', 'es', 'ar', 'fr', 'tr'];

// Helper function to check if a translation exists for all supported languages
function checkTranslationExists(key: string) {
  const missingTranslations: string[] = [];

  const translationEntry = (translations as Record<string, Record<string, string>>)[key];
  if (!translationEntry) {
    throw new Error(`Translation key "${key}" does not exist in translation.json`);
  }

  for (const lang of supportedLanguages) {
    if (!translationEntry[lang]) {
      missingTranslations.push(lang);
    }
  }

  return missingTranslations;
}

// Helper function to find duplicate translation keys
function findDuplicateKeys(obj: Record<string, any>) {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  // Only check top-level keys as these are our translation keys
  for (const key in obj) {
    if (seen.has(key)) {
      duplicates.add(key);
    } else {
      seen.add(key);
    }
  }

  return Array.from(duplicates);
}

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translationEntry = (translations as Record<string, Record<string, string>>)[key];
      return translationEntry?.ja || key;
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
          <UserAvatar onClick={() => {}} />
          <div data-testid="main-content">
            <h1>{t("LANDING$TITLE")}</h1>
            <button>{t("VSCODE$OPEN")}</button>
            <button>{t("SUGGESTIONS$INCREASE_TEST_COVERAGE")}</button>
            <button>{t("SUGGESTIONS$AUTO_MERGE_PRS")}</button>
            <button>{t("SUGGESTIONS$FIX_README")}</button>
            <button>{t("SUGGESTIONS$CLEAN_DEPENDENCIES")}</button>
          </div>
          <div data-testid="tabs">
            <span>{t("WORKSPACE$TERMINAL_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$BROWSER_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$JUPYTER_TAB_LABEL")}</span>
            <span>{t("WORKSPACE$CODE_EDITOR_TAB_LABEL")}</span>
          </div>
          <div data-testid="workspace-label">{t("WORKSPACE$TITLE")}</div>
          <button data-testid="new-project">{t("PROJECT$NEW_PROJECT")}</button>
          <div data-testid="status">
            <span>{t("TERMINAL$WAITING_FOR_CLIENT")}</span>
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
    expect(screen.getByText("テストカバレッジを向上させる")).toBeInTheDocument();
    expect(screen.getByText("Dependabot PRを自動マージ")).toBeInTheDocument();
    expect(screen.getByText("READMEを改善")).toBeInTheDocument();
    expect(screen.getByText("依存関係を整理")).toBeInTheDocument();

    // Check user avatar tooltip
    const userAvatar = screen.getByTestId("user-avatar");
    userAvatar.focus();
    expect(screen.getByText("アカウント設定")).toBeInTheDocument();

    // Check tab labels
    const tabs = screen.getByTestId("tabs");
    expect(tabs).toHaveTextContent("ターミナル");
    expect(tabs).toHaveTextContent("ブラウザ");
    expect(tabs).toHaveTextContent("Jupyter");
    expect(tabs).toHaveTextContent("コードエディタ");

    // Check workspace label and new project button
    expect(screen.getByTestId("workspace-label")).toHaveTextContent("ワークスペース");
    expect(screen.getByTestId("new-project")).toHaveTextContent("新規プロジェクト");

    // Check status messages
    const status = screen.getByTestId("status");
    expect(status).toHaveTextContent("クライアントの準備を待機中");
    expect(status).toHaveTextContent("接続済み");
    expect(status).toHaveTextContent("サーバーに接続済み");

    // Check account settings menu
    expect(screen.getByText("アカウント設定")).toBeInTheDocument();

    // Check time-related translations
    const time = screen.getByTestId("time");
    expect(time).toHaveTextContent("5 分前");
    expect(time).toHaveTextContent("2 時間前");
    expect(time).toHaveTextContent("3 日前");
  });

  test("all translation keys should have translations for all supported languages", () => {
    // Test all translation keys used in the component
    const translationKeys = [
      "LANDING$TITLE",
      "VSCODE$OPEN",
      "SUGGESTIONS$INCREASE_TEST_COVERAGE",
      "SUGGESTIONS$AUTO_MERGE_PRS",
      "SUGGESTIONS$FIX_README",
      "SUGGESTIONS$CLEAN_DEPENDENCIES",
      "WORKSPACE$TERMINAL_TAB_LABEL",
      "WORKSPACE$BROWSER_TAB_LABEL",
      "WORKSPACE$JUPYTER_TAB_LABEL",
      "WORKSPACE$CODE_EDITOR_TAB_LABEL",
      "WORKSPACE$TITLE",
      "PROJECT$NEW_PROJECT",
      "TERMINAL$WAITING_FOR_CLIENT",
      "STATUS$CONNECTED",
      "STATUS$CONNECTED_TO_SERVER",
      "TIME$MINUTES_AGO",
      "TIME$HOURS_AGO",
      "TIME$DAYS_AGO"
    ];

    // Check all keys and collect missing translations
    const missingTranslationsMap = new Map<string, string[]>();
    translationKeys.forEach(key => {
      const missing = checkTranslationExists(key);
      if (missing.length > 0) {
        missingTranslationsMap.set(key, missing);
      }
    });

    // If any translations are missing, throw an error with all missing translations
    if (missingTranslationsMap.size > 0) {
      const errorMessage = Array.from(missingTranslationsMap.entries())
        .map(([key, langs]) => `\n- "${key}" is missing translations for: ${langs.join(', ')}`)
        .join('');
      throw new Error(`Missing translations:${errorMessage}`);
    }
  });

  test("translation file should not have duplicate keys", () => {
    const duplicates = findDuplicateKeys(translations);

    if (duplicates.length > 0) {
      throw new Error(`Found duplicate translation keys: ${duplicates.join(', ')}`);
    }
  });
});
