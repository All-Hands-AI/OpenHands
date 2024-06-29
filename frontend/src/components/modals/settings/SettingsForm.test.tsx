import { screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { renderWithProviders } from "test-utils";
import Session from "#/services/session";
import SettingsForm from "./SettingsForm";

const onModelChangeMock = vi.fn();
const onAgentChangeMock = vi.fn();
const onLanguageChangeMock = vi.fn();
const onAPIKeyChangeMock = vi.fn();
const onResetSettingsMock = vi.fn();
const onSaveSettingsMock = vi.fn();
const onErrorMock = vi.fn();
const onThemeChangeMock = vi.fn();

const renderSettingsForm = (
  props?: Partial<React.ComponentProps<typeof SettingsForm>>,
) => {
  renderWithProviders(
    <SettingsForm
      disabled={false}
      settings={{
        LLM_MODEL: "model1",
        AGENT: "agent1",
        LANGUAGE: "en",
        LLM_API_KEY: "sk-...",
        THEME: "light",
      }}
      models={["model1", "model2", "model3"]}
      agents={["agent1", "agent2", "agent3"]}
      onModelChange={onModelChangeMock}
      onAgentChange={onAgentChangeMock}
      onLanguageChange={onLanguageChangeMock}
      onAPIKeyChange={onAPIKeyChangeMock}
      agentIsRunning={false}
      onResetSettings={onResetSettingsMock}
      onSaveSettings={onSaveSettingsMock}
      onError={onErrorMock}
      hasUnsavedChanges={false}
      theme="light"
      onThemeChange={onThemeChangeMock}
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...props}
    />,
  );
};

vi.spyOn(Session, "isConnected").mockImplementation(() => true);

describe("SettingsForm", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should display the first values in the array by default", () => {
    renderSettingsForm();

    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });
    const apiKeyInput = screen.getByTestId("apikey");

    expect(modelInput).toHaveValue("model1");
    expect(agentInput).toHaveValue("agent1");
    expect(languageInput).toHaveValue("English");
    expect(apiKeyInput).toHaveValue("sk-...");
  });

  it("should display the existing values if they are present", () => {
    renderSettingsForm({
      settings: {
        LLM_MODEL: "model2",
        AGENT: "agent2",
        LANGUAGE: "es",
        LLM_API_KEY: "sk-...",
        THEME: "dark",
      },
      theme: "dark",
    });

    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });

    expect(modelInput).toHaveValue("model2");
    expect(agentInput).toHaveValue("agent2");
    expect(languageInput).toHaveValue("Español");
  });

  it("should call onResetSettings when reset button is clicked", async () => {
    renderSettingsForm();
    const resetButton = screen.getByRole("button", { name: /reset/i });
    await userEvent.click(resetButton);
    expect(onResetSettingsMock).toHaveBeenCalled();
  });

  it("should call onSaveSettings when save button is clicked", async () => {
    renderSettingsForm();
    const saveButton = screen.getByRole("button", { name: /save/i });
    await userEvent.click(saveButton);
    expect(onSaveSettingsMock).toHaveBeenCalled();
  });

  it("should disable inputs when agentIsRunning is true", () => {
    renderSettingsForm({ agentIsRunning: true });
    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    expect(modelInput).toBeDisabled();
    expect(agentInput).toBeDisabled();
  });

  it("should show unsaved changes indicator when hasUnsavedChanges is true", () => {
    renderSettingsForm({ hasUnsavedChanges: true });
    const unsavedChangesIndicator = screen.getByText(/unsaved changes/i);
    expect(unsavedChangesIndicator).toBeInTheDocument();
  });

  describe("Form interactions", () => {
    describe("onChange handlers", () => {
      it("should call the onModelChange handler when the model changes", async () => {
        renderSettingsForm();

        const modelInput = screen.getByRole("combobox", { name: "model" });
        await act(async () => {
          await userEvent.click(modelInput);
        });

        const model3 = screen.getByText("model3");
        await act(async () => {
          await userEvent.click(model3);
        });

        expect(onModelChangeMock).toHaveBeenCalledWith("model3");
      });

      it("should call the onAgentChange handler when the agent changes", async () => {
        renderSettingsForm();

        const agentInput = screen.getByRole("combobox", { name: "agent" });
        await act(async () => {
          await userEvent.click(agentInput);
        });

        const agent3 = screen.getByText("agent3");
        await act(async () => {
          await userEvent.click(agent3);
        });

        expect(onAgentChangeMock).toHaveBeenCalledWith("agent3");
      });

      it("should call the onLanguageChange handler when the language changes", async () => {
        renderSettingsForm();

        const languageInput = screen.getByRole("combobox", {
          name: "language",
        });
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
  });
});
