import { render, screen, fireEvent } from "@testing-library/react";
import { SettingsForm } from "#/components/shared/modals/settings/settings-form";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider } from "react-i18next";
import i18n from "#/i18n";
import { SettingsProvider } from "#/context/settings-context";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter } from "react-router";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { rootReducer } from "#/store";

vi.mock("#/hooks/query/use-config", () => ({
  useConfig: () => ({
    data: {
      saas_mode: true,
    },
  }),
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
            <SettingsProvider>
              <SettingsForm
                settings={DEFAULT_SETTINGS}
                models={[]}
                agents={[]}
                securityAnalyzers={[]}
                onClose={() => {}}
              />
            </SettingsProvider>
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

  it("should show runtime size selector when advanced options are enabled", () => {
    renderSettingsForm();
    const advancedSwitch = screen.getByRole("switch", {
      name: "SETTINGS_FORM$ADVANCED_OPTIONS_LABEL",
    });
    fireEvent.click(advancedSwitch);
    expect(screen.getByText("SETTINGS_FORM$RUNTIME_SIZE_LABEL")).toBeInTheDocument();
  });
});
