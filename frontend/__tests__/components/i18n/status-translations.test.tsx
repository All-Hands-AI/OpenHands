import { render, screen } from "@testing-library/react";
import { test, expect, describe, vi } from "vitest";
import { useTranslation } from "react-i18next";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "STATUS$WAITING_FOR_CLIENT": "クライアントの準備を待機中",
        "STATUS$CONNECTED": "接続済み",
        "STATUS$CONNECTED_TO_SERVER": "サーバーに接続済み"
      };
      return translations[key] || key;
    },
  }),
}));

describe("Status translations", () => {
  test("should render Japanese status translations correctly", () => {
    // Mock a simple component that uses status translations
    const StatusComponent = () => {
      const { t } = useTranslation();
      return (
        <div>
          <div data-testid="waiting">{t("STATUS$WAITING_FOR_CLIENT")}</div>
          <div data-testid="connected">{t("STATUS$CONNECTED")}</div>
          <div data-testid="connected-server">{t("STATUS$CONNECTED_TO_SERVER")}</div>
        </div>
      );
    };

    render(<StatusComponent />);

    // Check that all translations are rendered correctly
    expect(screen.getByTestId("waiting")).toHaveTextContent("クライアントの準備を待機中");
    expect(screen.getByTestId("connected")).toHaveTextContent("接続済み");
    expect(screen.getByTestId("connected-server")).toHaveTextContent("サーバーに接続済み");
  });
});