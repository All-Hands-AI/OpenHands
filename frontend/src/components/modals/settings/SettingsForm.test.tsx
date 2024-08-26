import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { renderWithProviders } from "test-utils";
import { Settings } from "#/services/settings";
import SettingsForm from "./SettingsForm";

const onModelChangeMock = vi.fn();
const onCustomModelChangeMock = vi.fn();
const onModelTypeChangeMock = vi.fn();
const onAgentChangeMock = vi.fn();
const onLanguageChangeMock = vi.fn();
const onAPIKeyChangeMock = vi.fn();
const onConfirmationModeChangeMock = vi.fn();
const onSecurityAnalyzerChangeMock = vi.fn();

const renderSettingsForm = (settings?: Settings) => {
  renderWithProviders(
    <SettingsForm
      disabled={false}
      settings={
        settings || {
          LLM_MODEL: "gpt-4o",
          CUSTOM_LLM_MODEL: "",
          USING_CUSTOM_MODEL: false,
          AGENT: "agent1",
          LANGUAGE: "en",
          LLM_API_KEY: "sk-...",
          CONFIRMATION_MODE: true,
          SECURITY_ANALYZER: "analyzer1",
        }
      }
      models={["gpt-4o", "gpt-3.5-turbo", "azure/ada"]}
      agents={["agent1", "agent2", "agent3"]}
      securityAnalyzers={["analyzer1", "analyzer2", "analyzer3"]}
      onModelChange={onModelChangeMock}
      onCustomModelChange={onCustomModelChangeMock}
      onModelTypeChange={onModelTypeChangeMock}
      onAgentChange={onAgentChangeMock}
      onLanguageChange={onLanguageChangeMock}
      onAPIKeyChange={onAPIKeyChangeMock}
      onConfirmationModeChange={onConfirmationModeChangeMock}
      onSecurityAnalyzerChange={onSecurityAnalyzerChangeMock}
    />,
  );
};

describe("SettingsForm", () => {
  it("should display the first values in the array by default", () => {
    renderSettingsForm();

    const providerInput = screen.getByRole("combobox", { name: "Provider" });
    const modelInput = screen.getByRole("combobox", { name: "Model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });
    const apiKeyInput = screen.getByTestId("apikey");
    const confirmationModeInput = screen.getByTestId("confirmationmode");
    const securityAnalyzerInput = screen.getByRole("combobox", {
      name: "securityanalyzer",
    });

    expect(providerInput).toHaveValue("OpenAI");
    expect(modelInput).toHaveValue("gpt-4o");
    expect(agentInput).toHaveValue("agent1");
    expect(languageInput).toHaveValue("English");
    expect(apiKeyInput).toHaveValue("sk-...");
    expect(confirmationModeInput).toHaveAttribute("data-selected", "true");
    expect(securityAnalyzerInput).toHaveValue("analyzer1");
  });

  it("should display the existing values if they are present", () => {
    renderSettingsForm({
      LLM_MODEL: "gpt-3.5-turbo",
      CUSTOM_LLM_MODEL: "",
      USING_CUSTOM_MODEL: false,
      AGENT: "agent2",
      LANGUAGE: "es",
      LLM_API_KEY: "sk-...",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "analyzer2",
    });

    const providerInput = screen.getByRole("combobox", { name: "Provider" });
    const modelInput = screen.getByRole("combobox", { name: "Model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });
    const securityAnalyzerInput = screen.getByRole("combobox", {
      name: "securityanalyzer",
    });

    expect(providerInput).toHaveValue("OpenAI");
    expect(modelInput).toHaveValue("gpt-3.5-turbo");
    expect(agentInput).toHaveValue("agent2");
    expect(languageInput).toHaveValue("Español");
    expect(securityAnalyzerInput).toHaveValue("analyzer2");
  });

  it("should disable settings when disabled is true", () => {
    renderWithProviders(
      <SettingsForm
        settings={{
          LLM_MODEL: "gpt-4o",
          CUSTOM_LLM_MODEL: "",
          USING_CUSTOM_MODEL: false,
          AGENT: "agent1",
          LANGUAGE: "en",
          LLM_API_KEY: "sk-...",
          CONFIRMATION_MODE: true,
          SECURITY_ANALYZER: "analyzer1",
        }}
        models={["gpt-4o", "gpt-3.5-turbo", "azure/ada"]}
        agents={["agent1", "agent2", "agent3"]}
        securityAnalyzers={["analyzer1", "analyzer2", "analyzer3"]}
        disabled
        onModelChange={onModelChangeMock}
        onCustomModelChange={onCustomModelChangeMock}
        onModelTypeChange={onModelTypeChangeMock}
        onAgentChange={onAgentChangeMock}
        onLanguageChange={onLanguageChangeMock}
        onAPIKeyChange={onAPIKeyChangeMock}
        onConfirmationModeChange={onConfirmationModeChangeMock}
        onSecurityAnalyzerChange={onSecurityAnalyzerChangeMock}
      />,
    );

    const providerInput = screen.getByRole("combobox", { name: "Provider" });
    const modelInput = screen.getByRole("combobox", { name: "Model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });
    const confirmationModeInput = screen.getByTestId("confirmationmode");
    const securityAnalyzerInput = screen.getByRole("combobox", {
      name: "securityanalyzer",
    });

    expect(providerInput).toBeDisabled();
    expect(modelInput).toBeDisabled();
    expect(agentInput).toBeDisabled();
    expect(languageInput).toBeDisabled();
    expect(confirmationModeInput).toHaveAttribute("data-disabled", "true");
    expect(securityAnalyzerInput).toBeDisabled();
  });

  describe("onChange handlers", () => {
    it("should call the onAgentChange handler when the agent changes", async () => {
      const user = userEvent.setup();
      renderSettingsForm();

      // We need to enable the agent select
      const agentSwitch = screen.getByTestId("enableagentselect");
      await user.click(agentSwitch);

      const agentInput = screen.getByRole("combobox", { name: "agent" });
      await user.click(agentInput);

      const agent3 = screen.getByText("agent3");
      await user.click(agent3);

      expect(onAgentChangeMock).toHaveBeenCalledWith("agent3");
    });

    it("should call the onLanguageChange handler when the language changes", async () => {
      renderSettingsForm();

      const languageInput = screen.getByRole("combobox", { name: "language" });
      await act(async () => {
        await userEvent.click(languageInput);
      });

      const french = screen.getByText("Français");
      await act(async () => {
        await userEvent.click(french);
      });

      expect(onLanguageChangeMock).toHaveBeenCalledWith("Français");
    });

    it("should call the onAPIKeyChange handler when the API key changes", async () => {
      renderSettingsForm();

      const apiKeyInput = screen.getByTestId("apikey");
      await act(async () => {
        await userEvent.type(apiKeyInput, "x");
      });

      expect(onAPIKeyChangeMock).toHaveBeenCalledWith("sk-...x");
    });
  });

  describe("Setting a custom LLM model", () => {
    it("should display the fetched models by default", () => {
      renderSettingsForm();

      const modelSelector = screen.getByTestId("model-selector");
      expect(modelSelector).toBeInTheDocument();

      const customModelInput = screen.queryByTestId("custom-model-input");
      expect(customModelInput).not.toBeInTheDocument();
    });

    it("should switch to the custom model input when the custom model toggle is clicked", async () => {
      const user = userEvent.setup();
      renderSettingsForm();

      const customModelToggle = screen.getByTestId("custom-model-toggle");
      await user.click(customModelToggle);

      const modelSelector = screen.queryByTestId("model-selector");
      expect(modelSelector).not.toBeInTheDocument();

      const customModelInput = screen.getByTestId("custom-model-input");
      expect(customModelInput).toBeInTheDocument();
    });

    it("should call the onCustomModelChange handler when the custom model input changes", async () => {
      const user = userEvent.setup();
      renderSettingsForm();

      const customModelToggle = screen.getByTestId("custom-model-toggle");
      await user.click(customModelToggle);

      const customModelInput = screen.getByTestId("custom-model-input");
      await userEvent.type(customModelInput, "my/custom-model");

      expect(onCustomModelChangeMock).toHaveBeenCalledWith("my/custom-model");
      expect(onModelTypeChangeMock).toHaveBeenCalledWith("custom");
    });

    it("should have custom model switched if using custom model", () => {
      renderWithProviders(
        <SettingsForm
          settings={{
            LLM_MODEL: "gpt-4o",
            CUSTOM_LLM_MODEL: "CUSTOM_MODEL",
            USING_CUSTOM_MODEL: true,
            AGENT: "agent1",
            LANGUAGE: "en",
            LLM_API_KEY: "sk-...",
            CONFIRMATION_MODE: true,
            SECURITY_ANALYZER: "analyzer1",
          }}
          models={["gpt-4o", "gpt-3.5-turbo", "azure/ada"]}
          agents={["agent1", "agent2", "agent3"]}
          securityAnalyzers={["analyzer1", "analyzer2", "analyzer3"]}
          disabled
          onModelChange={onModelChangeMock}
          onCustomModelChange={onCustomModelChangeMock}
          onModelTypeChange={onModelTypeChangeMock}
          onAgentChange={onAgentChangeMock}
          onLanguageChange={onLanguageChangeMock}
          onAPIKeyChange={onAPIKeyChangeMock}
          onConfirmationModeChange={onConfirmationModeChangeMock}
          onSecurityAnalyzerChange={onSecurityAnalyzerChangeMock}
        />,
      );

      const customModelToggle = screen.getByTestId("custom-model-toggle");
      expect(customModelToggle).toHaveAttribute("aria-checked", "true");
    });
  });
});
