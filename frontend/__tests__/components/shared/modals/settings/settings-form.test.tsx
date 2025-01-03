import { render, screen, fireEvent } from "@testing-library/react";
import { SettingsForm } from "#/components/shared/modals/settings/settings-form";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider } from "react-i18next";
import i18n from "#/i18n";
import { SettingsUpToDateProvider } from "#/context/settings-up-to-date-context";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter } from "react-router";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { rootReducer } from "#/store";

vi.mock("#/hooks/query/use-config", () => ({
  useConfig: () => ({
    data: {
      APP_MODE: "saas",
    },
  }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
  // This mock makes sure that using the I18nextProvider in the test works
  I18nextProvider: ({ children }: { children: React.ReactNode }) => children,
  initReactI18next: {
    type: "3rdParty",
    init: () => {},
  },
}));

vi.mock("#/i18n", () => ({
  default: {
    use: () => ({
      init: () => {},
    }),
  },
}));

const queryClient = new QueryClient();
const store = configureStore({
  reducer: rootReducer,
});

const renderSettingsForm = () => {
  return render(
    <Provider store={store}>
      <MemoryRouter>
        <QueryClientProvider client={queryClient}>
          <I18nextProvider i18n={i18n}>
            <SettingsUpToDateProvider>
              <SettingsForm
                settings={DEFAULT_SETTINGS}
                models={[]}
                agents={[]}
                securityAnalyzers={[]}
                onClose={() => {}}
              />
            </SettingsUpToDateProvider>
          </I18nextProvider>
        </QueryClientProvider>
      </MemoryRouter>
    </Provider>
  );
};

describe("SettingsForm", () => {
  it("should not show runtime size selector by default", () => {
    renderSettingsForm();
    expect(screen.queryByText("Runtime Size")).not.toBeInTheDocument();
  });

  it("should show runtime size selector when advanced options are enabled", async () => {
    renderSettingsForm();
    const advancedSwitch = screen.getByRole("switch", {
      name: "SETTINGS_FORM$ADVANCED_OPTIONS_LABEL",
    });
    fireEvent.click(advancedSwitch);
    console.log("Advanced switch clicked");
    screen.debug();
    await screen.findByText("SETTINGS_FORM$RUNTIME_SIZE_LABEL");
  });
});
