// See https://redux.js.org/usage/writing-tests#setting-up-a-reusable-test-render-function for more information

import React, { PropsWithChildren } from "react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { RenderOptions, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider, initReactI18next } from "react-i18next";
import i18n from "i18next";
import { expect, vi } from "vitest";
import { AxiosError } from "axios";
import userEvent from "@testing-library/user-event";
import { AppStore, RootState, rootReducer } from "./src/store";
import { INITIAL_MOCK_ORGS } from "#/mocks/org-handlers";

// Mock useParams before importing components
vi.mock("react-router", async () => {
  const actual =
    await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useParams: () => ({ conversationId: "test-conversation-id" }),
    useRevalidator: () => ({
      revalidate: vi.fn(),
    }),
  };
});

// Initialize i18n for tests
i18n.use(initReactI18next).init({
  lng: "en",
  fallbackLng: "en",
  ns: ["translation"],
  defaultNS: "translation",
  resources: {
    en: {
      translation: {},
    },
  },
  interpolation: {
    escapeValue: false,
  },
});

export const setupStore = (preloadedState?: Partial<RootState>): AppStore =>
  configureStore({
    reducer: rootReducer,
    preloadedState,
  });

// This type interface extends the default options for render from RTL, as well
// as allows the user to specify other things such as initialState, store.
interface ExtendedRenderOptions extends Omit<RenderOptions, "queries"> {
  preloadedState?: Partial<RootState>;
  store?: AppStore;
}

// Export our own customized renderWithProviders function that creates a new Redux store and renders a <Provider>
// Note that this creates a separate Redux store instance for every test, rather than reusing the same store instance and resetting its state
export function renderWithProviders(
  ui: React.ReactElement,
  {
    preloadedState = {},
    // Automatically create a store instance if no store was passed in
    store = setupStore(preloadedState),
    ...renderOptions
  }: ExtendedRenderOptions = {},
) {
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <Provider store={store}>
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
        </QueryClientProvider>
      </Provider>
    );
  }
  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}

export const createAxiosNotFoundErrorObject = () =>
  new AxiosError(
    "Request failed with status code 404",
    "ERR_BAD_REQUEST",
    undefined,
    undefined,
    {
      status: 404,
      statusText: "Not Found",
      data: { message: "Settings not found" },
      headers: {},
      // @ts-expect-error - we only need the response object for this test
      config: {},
    },
  );

export const selectOrganization = async ({
  orgIndex,
}: {
  orgIndex: number;
}) => {
  const organizationSelect = await screen.findByTestId("org-select");
  expect(organizationSelect).toBeInTheDocument();

  await userEvent.click(organizationSelect);

  // Wait for the options to appear in the popover
  const targetOrg = INITIAL_MOCK_ORGS[orgIndex];
  if (!targetOrg) {
    expect.fail(`No organization found at index ${orgIndex}`);
  }

  // Find the option by its text content (organization name)
  const option = await screen.findByText(targetOrg.name);
  await userEvent.click(option);
};
