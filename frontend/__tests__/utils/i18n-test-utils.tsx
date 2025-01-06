import { ReactNode } from "react";
import { I18nextProvider } from "react-i18next";

const mockT = (key: string) => {
  const translations: Record<string, string> = {
    "SUGGESTIONS$TODO_APP": "ToDoリストアプリを開発する",
    "LANDING$BUILD_APP_BUTTON": "プルリクエストを表示するアプリを開発する",
    "SUGGESTIONS$HACKER_NEWS": "Hacker Newsのトップ記事を表示するbashスクリプトを作成する",
  };
  return translations[key] || key;
};

const mockI18n = {
  language: "ja",
  t: mockT,
  exists: () => true,
};

export function I18nTestProvider({ children }: { children: ReactNode }) {
  return (
    <I18nextProvider i18n={mockI18n as any}>{children}</I18nextProvider>
  );
}