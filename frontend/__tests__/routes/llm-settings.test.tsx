import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import LlmSettingsScreen from "#/routes/llm-settings";
import OpenHands from "#/api/open-hands";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import { AuthProvider } from "#/context/auth-context";
import * as AdvancedSettingsUtlls from "#/utils/has-advanced-settings-set";

const renderLlmSettingsScreen = () =>
  render(<LlmSettingsScreen />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    ),
  });

beforeEach(() => {
  vi.resetAllMocks();
});

describe("Content", () => {
  describe("Basic form", () => {
    it("should render the basic form by default", async () => {
      renderLlmSettingsScreen();
      await screen.findByTestId("llm-settings-screen");

      const basicFom = screen.getByTestId("llm-settings-form-basic");
      within(basicFom).getByTestId("llm-provider-input");
      within(basicFom).getByTestId("llm-model-input");
      within(basicFom).getByTestId("llm-api-key-input");
      within(basicFom).getByTestId("llm-api-key-help-anchor");
    });

    it("should render the default values if non exist", async () => {
      renderLlmSettingsScreen();
      await screen.findByTestId("llm-settings-screen");

      const provider = screen.getByTestId("llm-provider-input");
      const model = screen.getByTestId("llm-model-input");
      const apiKey = screen.getByTestId("llm-api-key-input");

      await waitFor(() => {
        expect(provider).toHaveValue("Anthropic");
        expect(model).toHaveValue("claude-3-5-sonnet-20241022");

        expect(apiKey).toHaveValue("");
        expect(apiKey).toHaveProperty("placeholder", "");
      });
    });

    it("should render the existing settings values", async () => {
      const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_model: "openai/gpt-4o",
        llm_api_key_set: true,
      });

      renderLlmSettingsScreen();
      await screen.findByTestId("llm-settings-screen");

      const provider = screen.getByTestId("llm-provider-input");
      const model = screen.getByTestId("llm-model-input");
      const apiKey = screen.getByTestId("llm-api-key-input");

      await waitFor(() => {
        expect(provider).toHaveValue("OpenAI");
        expect(model).toHaveValue("gpt-4o");

        expect(apiKey).toHaveValue("");
        expect(apiKey).toHaveProperty("placeholder", "<hidden>");
      });
    });
  });

  describe("Advanced form", () => {
    it("should render the advanced form if the switch is toggled", async () => {
      renderLlmSettingsScreen();
      await screen.findByTestId("llm-settings-screen");

      const advancedSwitch = screen.getByTestId("advanced-settings-switch");
      const basicForm = screen.getByTestId("llm-settings-form-basic");

      expect(
        screen.queryByTestId("llm-settings-form-advanced"),
      ).not.toBeInTheDocument();
      expect(basicForm).toBeInTheDocument();

      await userEvent.click(advancedSwitch);

      expect(
        screen.queryByTestId("llm-settings-form-advanced"),
      ).toBeInTheDocument();
      expect(basicForm).not.toBeInTheDocument();

      const advancedForm = screen.getByTestId("llm-settings-form-advanced");
      within(advancedForm).getByTestId("llm-custom-model-input");
      within(advancedForm).getByTestId("base-url-input");
      within(advancedForm).getByTestId("llm-api-key-input");
      within(advancedForm).getByTestId("llm-api-key-help-anchor");
      within(advancedForm).getByTestId("agent-input");
      within(advancedForm).getByTestId("enable-confirmation-mode-switch");
      within(advancedForm).getByTestId("enable-memory-condenser-switch");

      await userEvent.click(advancedSwitch);
      expect(
        screen.queryByTestId("llm-settings-form-advanced"),
      ).not.toBeInTheDocument();
      expect(screen.getByTestId("llm-settings-form-basic")).toBeInTheDocument();
    });

    it("should render the default advanced settings", async () => {
      renderLlmSettingsScreen();
      await screen.findByTestId("llm-settings-screen");

      const advancedSwitch = screen.getByTestId("advanced-settings-switch");
      expect(advancedSwitch).not.toBeChecked();

      await userEvent.click(advancedSwitch);

      const model = screen.getByTestId("llm-custom-model-input");
      const baseUrl = screen.getByTestId("base-url-input");
      const apiKey = screen.getByTestId("llm-api-key-input");
      const agent = screen.getByTestId("agent-input");
      const confirmation = screen.getByTestId(
        "enable-confirmation-mode-switch",
      );
      const condensor = screen.getByTestId("enable-memory-condenser-switch");

      expect(model).toHaveValue("anthropic/claude-3-5-sonnet-20241022");
      expect(baseUrl).toHaveValue("");
      expect(apiKey).toHaveValue("");
      expect(apiKey).toHaveProperty("placeholder", "");
      expect(agent).toHaveValue("CodeActAgent");
      expect(confirmation).not.toBeChecked();
      expect(condensor).toBeChecked();
    });

    it("should render the advanced form if existings settings are advanced", async () => {
      const hasAdvancedSettingsSetSpy = vi.spyOn(
        AdvancedSettingsUtlls,
        "hasAdvancedSettingsSet",
      );
      hasAdvancedSettingsSetSpy.mockReturnValue(true);

      renderLlmSettingsScreen();

      await waitFor(() => {
        const advancedSwitch = screen.getByTestId("advanced-settings-switch");
        expect(advancedSwitch).toBeChecked();
        screen.getByTestId("llm-settings-form-advanced");
      });
    });

    it("should render existing advanced settings correctly", async () => {
      const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
      getSettingsSpy.mockResolvedValue({
        ...MOCK_DEFAULT_USER_SETTINGS,
        llm_model: "openai/gpt-4o",
        llm_base_url: "https://api.openai.com/v1/chat/completions",
        llm_api_key_set: true,
        agent: "CoActAgent",
        confirmation_mode: true,
        enable_default_condenser: false,
      });

      renderLlmSettingsScreen();
      await screen.findByTestId("llm-settings-screen");

      const model = screen.getByTestId("llm-custom-model-input");
      const baseUrl = screen.getByTestId("base-url-input");
      const apiKey = screen.getByTestId("llm-api-key-input");
      const agent = screen.getByTestId("agent-input");
      const confirmation = screen.getByTestId(
        "enable-confirmation-mode-switch",
      );
      const condensor = screen.getByTestId("enable-memory-condenser-switch");

      await waitFor(() => {
        expect(model).toHaveValue("openai/gpt-4o");
        expect(baseUrl).toHaveValue(
          "https://api.openai.com/v1/chat/completions",
        );
        expect(apiKey).toHaveValue("");
        expect(apiKey).toHaveProperty("placeholder", "<hidden>");
        expect(agent).toHaveValue("CoActAgent");
        expect(confirmation).toBeChecked();
        expect(condensor).not.toBeChecked();
      });
    });
  });
});

describe("Form submission", () => {
  it.todo("should submit the basic form with the correct values");
  it.todo("should submit the advanced form with the correct values");
  it.todo(
    "should disable the button if there are no changes in the basic form",
  );
  it.todo(
    "should disable the button if there are no changes in the advanced form",
  );
  it.todo("should disable the button when submitting changes");
});

describe.todo("Status toasts", () => {
  it.todo("should call displaySuccessToast when the settings are saved");
  it.todo("should call displayErrorToast when the settings are saved");
});
