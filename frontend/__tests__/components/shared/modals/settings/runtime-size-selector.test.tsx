import { render, screen } from "@testing-library/react";
import { RuntimeSizeSelector } from "#/components/shared/modals/settings/runtime-size-selector";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider } from "react-i18next";
import i18n from "#/i18n";
import { describe, it, expect, vi } from "vitest";

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

const renderRuntimeSizeSelector = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>
        <RuntimeSizeSelector isDisabled={false} />
      </I18nextProvider>
    </QueryClientProvider>
  );
};

describe("RuntimeSizeSelector", () => {
  it("should show both runtime size options", () => {
    renderRuntimeSizeSelector();
    // The options are in the hidden select element
    const select = screen.getByRole("combobox", { hidden: true });
    expect(select).toHaveValue("1");
    expect(select).toHaveDisplayValue("1x (2 core, 8G)");
    expect(select.children).toHaveLength(3); // Empty option + 2 size options
  });

  it("should show the full description text for disabled options", async () => {
    renderRuntimeSizeSelector();

    // Find the hidden select container
    const container = screen.getByTestId("hidden-select-container");
    const select = container.querySelector("select");
    expect(select).toBeInTheDocument();

    // Find the disabled option
    const option = select?.querySelector('option[value="2"]');
    expect(option).toBeInTheDocument();
    expect(option).toHaveTextContent("2x (4 core, 16G)");

  });
});
