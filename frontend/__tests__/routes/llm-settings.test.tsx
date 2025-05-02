import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import LlmSettingsScreen from "#/routes/llm-settings";
import OpenHands from "#/api/open-hands";
import {
  MOCK_DEFAULT_USER_SETTINGS,
  resetTestHandlersMockSettings,
} from "#/mocks/handlers";
import { AuthProvider } from "#/context/auth-context";
import * as AdvancedSettingsUtlls from "#/utils/has-advanced-settings-set";
import * as ToastHandlers from "#/utils/custom-toast-handlers";

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
  resetTestHandlersMockSettings();
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
        expect(screen.getByTestId("set-indicator")).toBeInTheDocument();
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

      // check that security analyzer is present
      expect(
        screen.queryByTestId("security-analyzer-input"),
      ).not.toBeInTheDocument();
      await userEvent.click(confirmation);
      screen.getByTestId("security-analyzer-input");
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
        security_analyzer: "mock-invariant",
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
      const securityAnalyzer = screen.getByTestId("security-analyzer-input");

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
        expect(securityAnalyzer).toHaveValue("mock-invariant");
      });
    });
  });

  it.todo("should render an indicator if the llm api key is set");
});

describe("Form submission", () => {
  it("should submit the basic form with the correct values", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");

    const provider = screen.getByTestId("llm-provider-input");
    const model = screen.getByTestId("llm-model-input");
    const apiKey = screen.getByTestId("llm-api-key-input");

    // select provider
    await userEvent.click(provider);
    const providerOption = screen.getByText("OpenAI");
    await userEvent.click(providerOption);
    expect(provider).toHaveValue("OpenAI");

    // enter api key
    await userEvent.type(apiKey, "test-api-key");

    // select model
    await userEvent.click(model);
    const modelOption = screen.getByText("gpt-4o");
    await userEvent.click(modelOption);
    expect(model).toHaveValue("gpt-4o");

    const submitButton = screen.getByTestId("submit-button");
    await userEvent.click(submitButton);

    expect(saveSettingsSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        llm_model: "openai/gpt-4o",
        llm_api_key: "test-api-key",
      }),
    );
  });

  it("should submit the advanced form with the correct values", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");

    const advancedSwitch = screen.getByTestId("advanced-settings-switch");
    await userEvent.click(advancedSwitch);

    const model = screen.getByTestId("llm-custom-model-input");
    const baseUrl = screen.getByTestId("base-url-input");
    const apiKey = screen.getByTestId("llm-api-key-input");
    const agent = screen.getByTestId("agent-input");
    const confirmation = screen.getByTestId("enable-confirmation-mode-switch");
    const condensor = screen.getByTestId("enable-memory-condenser-switch");

    // enter custom model
    await userEvent.clear(model);
    await userEvent.type(model, "openai/gpt-4o");
    expect(model).toHaveValue("openai/gpt-4o");

    // enter base url
    await userEvent.type(baseUrl, "https://api.openai.com/v1/chat/completions");
    expect(baseUrl).toHaveValue("https://api.openai.com/v1/chat/completions");

    // enter api key
    await userEvent.type(apiKey, "test-api-key");

    // toggle confirmation mode
    await userEvent.click(confirmation);
    expect(confirmation).toBeChecked();

    // toggle memory condensor
    await userEvent.click(condensor);
    expect(condensor).not.toBeChecked();

    // select agent
    await userEvent.click(agent);
    const agentOption = screen.getByText("CoActAgent");
    await userEvent.click(agentOption);
    expect(agent).toHaveValue("CoActAgent");

    // select security analyzer
    const securityAnalyzer = screen.getByTestId("security-analyzer-input");
    await userEvent.click(securityAnalyzer);
    const securityAnalyzerOption = screen.getByText("mock-invariant");
    await userEvent.click(securityAnalyzerOption);

    const submitButton = screen.getByTestId("submit-button");
    await userEvent.click(submitButton);

    expect(saveSettingsSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        llm_model: "openai/gpt-4o",
        llm_base_url: "https://api.openai.com/v1/chat/completions",
        agent: "CoActAgent",
        confirmation_mode: true,
        enable_default_condenser: false,
        security_analyzer: "mock-invariant",
      }),
    );
  });

  it("should disable the button if there are no changes in the basic form", async () => {
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      llm_model: "openai/gpt-4o",
      llm_api_key_set: true,
    });

    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");
    screen.getByTestId("llm-settings-form-basic");

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toBeDisabled();

    const model = screen.getByTestId("llm-model-input");
    const apiKey = screen.getByTestId("llm-api-key-input");

    // select model
    await userEvent.click(model);
    const modelOption = screen.getByText("gpt-4o-mini");
    await userEvent.click(modelOption);
    expect(model).toHaveValue("gpt-4o-mini");
    expect(submitButton).not.toBeDisabled();

    // reset model
    await userEvent.click(model);
    const modelOption2 = screen.getByText("gpt-4o");
    await userEvent.click(modelOption2);
    expect(model).toHaveValue("gpt-4o");
    expect(submitButton).toBeDisabled();

    // set api key
    await userEvent.type(apiKey, "test-api-key");
    expect(apiKey).toHaveValue("test-api-key");
    expect(submitButton).not.toBeDisabled();

    // reset api key
    await userEvent.clear(apiKey);
    expect(apiKey).toHaveValue("");
    expect(submitButton).toBeDisabled();
  });

  it("should disable the button if there are no changes in the advanced form", async () => {
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      llm_model: "openai/gpt-4o",
      llm_base_url: "https://api.openai.com/v1/chat/completions",
      llm_api_key_set: true,
      confirmation_mode: true,
    });

    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");
    screen.getByTestId("llm-settings-form-advanced");

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toBeDisabled();

    const model = screen.getByTestId("llm-custom-model-input");
    const baseUrl = screen.getByTestId("base-url-input");
    const apiKey = screen.getByTestId("llm-api-key-input");
    const agent = screen.getByTestId("agent-input");
    const confirmation = screen.getByTestId("enable-confirmation-mode-switch");
    const condensor = screen.getByTestId("enable-memory-condenser-switch");

    // enter custom model
    await userEvent.type(model, "-mini");
    expect(model).toHaveValue("openai/gpt-4o-mini");
    expect(submitButton).not.toBeDisabled();

    // reset model
    await userEvent.clear(model);
    expect(model).toHaveValue("");
    expect(submitButton).toBeDisabled();

    await userEvent.type(model, "openai/gpt-4o");
    expect(model).toHaveValue("openai/gpt-4o");
    expect(submitButton).toBeDisabled();

    // enter base url
    await userEvent.type(baseUrl, "/extra");
    expect(baseUrl).toHaveValue(
      "https://api.openai.com/v1/chat/completions/extra",
    );
    expect(submitButton).not.toBeDisabled();

    await userEvent.clear(baseUrl);
    expect(baseUrl).toHaveValue("");
    expect(submitButton).not.toBeDisabled();

    await userEvent.type(baseUrl, "https://api.openai.com/v1/chat/completions");
    expect(baseUrl).toHaveValue("https://api.openai.com/v1/chat/completions");
    expect(submitButton).toBeDisabled();

    // set api key
    await userEvent.type(apiKey, "test-api-key");
    expect(apiKey).toHaveValue("test-api-key");
    expect(submitButton).not.toBeDisabled();

    // reset api key
    await userEvent.clear(apiKey);
    expect(apiKey).toHaveValue("");
    expect(submitButton).toBeDisabled();

    // set agent
    await userEvent.clear(agent);
    await userEvent.type(agent, "test-agent");
    expect(agent).toHaveValue("test-agent");
    expect(submitButton).not.toBeDisabled();

    // reset agent
    await userEvent.clear(agent);
    expect(agent).toHaveValue("");
    expect(submitButton).toBeDisabled();

    await userEvent.type(agent, "CodeActAgent");
    expect(agent).toHaveValue("CodeActAgent");
    expect(submitButton).toBeDisabled();

    // toggle confirmation mode
    await userEvent.click(confirmation);
    expect(confirmation).not.toBeChecked();
    expect(submitButton).not.toBeDisabled();
    await userEvent.click(confirmation);
    expect(confirmation).toBeChecked();
    expect(submitButton).toBeDisabled();

    // toggle memory condensor
    await userEvent.click(condensor);
    expect(condensor).not.toBeChecked();
    expect(submitButton).not.toBeDisabled();
    await userEvent.click(condensor);
    expect(condensor).toBeChecked();
    expect(submitButton).toBeDisabled();

    // select security analyzer
    const securityAnalyzer = screen.getByTestId("security-analyzer-input");
    await userEvent.click(securityAnalyzer);
    const securityAnalyzerOption = screen.getByText("mock-invariant");
    await userEvent.click(securityAnalyzerOption);
    expect(securityAnalyzer).toHaveValue("mock-invariant");

    expect(submitButton).not.toBeDisabled();

    await userEvent.clear(securityAnalyzer);
    expect(securityAnalyzer).toHaveValue("");
    expect(submitButton).toBeDisabled();
  });

  it("should reset button state when switching between forms", async () => {
    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");

    const advancedSwitch = screen.getByTestId("advanced-settings-switch");
    const submitButton = screen.getByTestId("submit-button");

    expect(submitButton).toBeDisabled();

    // dirty the basic form
    const apiKey = screen.getByTestId("llm-api-key-input");
    await userEvent.type(apiKey, "test-api-key");
    expect(submitButton).not.toBeDisabled();

    await userEvent.click(advancedSwitch);
    expect(submitButton).toBeDisabled();

    // dirty the advanced form
    const model = screen.getByTestId("llm-custom-model-input");
    await userEvent.type(model, "openai/gpt-4o");
    expect(submitButton).not.toBeDisabled();

    await userEvent.click(advancedSwitch);
    expect(submitButton).toBeDisabled();
  });

  // flaky test
  it.skip("should disable the button when submitting changes", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");

    const apiKey = screen.getByTestId("llm-api-key-input");
    await userEvent.type(apiKey, "test-api-key");

    const submitButton = screen.getByTestId("submit-button");
    await userEvent.click(submitButton);

    expect(saveSettingsSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        llm_api_key: "test-api-key",
      }),
    );

    expect(submitButton).toHaveTextContent("Saving...");
    expect(submitButton).toBeDisabled();

    await waitFor(() => {
      expect(submitButton).toHaveTextContent("Save");
      expect(submitButton).toBeDisabled();
    });
  });

  it("should clear advanced settings when saving basic settings", async () => {
    const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
    getSettingsSpy.mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      llm_model: "openai/gpt-4o",
      llm_base_url: "https://api.openai.com/v1/chat/completions",
      llm_api_key_set: true,
      confirmation_mode: true,
    });
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    renderLlmSettingsScreen();

    await screen.findByTestId("llm-settings-screen");
    const advancedSwitch = screen.getByTestId("advanced-settings-switch");
    await userEvent.click(advancedSwitch);

    const provider = screen.getByTestId("llm-provider-input");
    const model = screen.getByTestId("llm-model-input");

    // select provider
    await userEvent.click(provider);
    const providerOption = screen.getByText("Anthropic");
    await userEvent.click(providerOption);

    // select model
    await userEvent.click(model);
    const modelOption = screen.getByText("claude-3-5-sonnet-20241022");
    await userEvent.click(modelOption);

    const submitButton = screen.getByTestId("submit-button");
    await userEvent.click(submitButton);

    expect(saveSettingsSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        llm_model: "anthropic/claude-3-5-sonnet-20241022",
        llm_base_url: "",
        confirmation_mode: false,
      }),
    );
  });
});

describe("Status toasts", () => {
  describe("Basic form", () => {
    it("should call displaySuccessToast when the settings are saved", async () => {
      const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

      const displaySuccessToastSpy = vi.spyOn(
        ToastHandlers,
        "displaySuccessToast",
      );

      renderLlmSettingsScreen();

      // Toggle setting to change
      const apiKeyInput = await screen.findByTestId("llm-api-key-input");
      await userEvent.type(apiKeyInput, "test-api-key");

      const submit = await screen.findByTestId("submit-button");
      await userEvent.click(submit);

      expect(saveSettingsSpy).toHaveBeenCalled();
      await waitFor(() => expect(displaySuccessToastSpy).toHaveBeenCalled());
    });

    it("should call displayErrorToast when the settings fail to save", async () => {
      const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

      const displayErrorToastSpy = vi.spyOn(ToastHandlers, "displayErrorToast");

      saveSettingsSpy.mockRejectedValue(new Error("Failed to save settings"));

      renderLlmSettingsScreen();

      // Toggle setting to change
      const apiKeyInput = await screen.findByTestId("llm-api-key-input");
      await userEvent.type(apiKeyInput, "test-api-key");

      const submit = await screen.findByTestId("submit-button");
      await userEvent.click(submit);

      expect(saveSettingsSpy).toHaveBeenCalled();
      expect(displayErrorToastSpy).toHaveBeenCalled();
    });
  });

  describe("Advanced form", () => {
    it("should call displaySuccessToast when the settings are saved", async () => {
      const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

      const displaySuccessToastSpy = vi.spyOn(
        ToastHandlers,
        "displaySuccessToast",
      );

      renderLlmSettingsScreen();
      await screen.findByTestId("llm-settings-screen");

      const advancedSwitch = screen.getByTestId("advanced-settings-switch");
      await userEvent.click(advancedSwitch);
      await screen.findByTestId("llm-settings-form-advanced");

      // Toggle setting to change
      const apiKeyInput = await screen.findByTestId("llm-api-key-input");
      await userEvent.type(apiKeyInput, "test-api-key");

      const submit = await screen.findByTestId("submit-button");
      await userEvent.click(submit);

      expect(saveSettingsSpy).toHaveBeenCalled();
      await waitFor(() => expect(displaySuccessToastSpy).toHaveBeenCalled());
    });

    it("should call displayErrorToast when the settings fail to save", async () => {
      const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");

      const displayErrorToastSpy = vi.spyOn(ToastHandlers, "displayErrorToast");

      saveSettingsSpy.mockRejectedValue(new Error("Failed to save settings"));

      renderLlmSettingsScreen();
      await screen.findByTestId("llm-settings-screen");

      const advancedSwitch = screen.getByTestId("advanced-settings-switch");
      await userEvent.click(advancedSwitch);
      await screen.findByTestId("llm-settings-form-advanced");

      // Toggle setting to change
      const apiKeyInput = await screen.findByTestId("llm-api-key-input");
      await userEvent.type(apiKeyInput, "test-api-key");

      const submit = await screen.findByTestId("submit-button");
      await userEvent.click(submit);

      expect(saveSettingsSpy).toHaveBeenCalled();
      expect(displayErrorToastSpy).toHaveBeenCalled();
    });
  });
});

describe("SaaS mode", () => {
  it("should not render the runtime settings input in oss mode", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return mode
    getConfigSpy.mockResolvedValue({
      APP_MODE: "oss",
    });

    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");

    const advancedSwitch = screen.getByTestId("advanced-settings-switch");
    await userEvent.click(advancedSwitch);
    await screen.findByTestId("llm-settings-form-advanced");

    const runtimeSettingsInput = screen.queryByTestId("runtime-settings-input");
    expect(runtimeSettingsInput).not.toBeInTheDocument();
  });

  it("should render the runtime settings input in saas mode", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return mode
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
    });

    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");

    const advancedSwitch = screen.getByTestId("advanced-settings-switch");
    await userEvent.click(advancedSwitch);
    await screen.findByTestId("llm-settings-form-advanced");

    const runtimeSettingsInput = screen.queryByTestId("runtime-settings-input");
    expect(runtimeSettingsInput).toBeInTheDocument();
  });

  it("should always render the runtime settings input as disabled", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - only return mode
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
    });

    renderLlmSettingsScreen();
    await screen.findByTestId("llm-settings-screen");

    const advancedSwitch = screen.getByTestId("advanced-settings-switch");
    await userEvent.click(advancedSwitch);
    await screen.findByTestId("llm-settings-form-advanced");

    const runtimeSettingsInput = screen.queryByTestId("runtime-settings-input");
    expect(runtimeSettingsInput).toBeInTheDocument();
    expect(runtimeSettingsInput).toBeDisabled();
  });
});
