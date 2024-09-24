import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import i18next from "i18next";
import React from "react";
import { renderWithProviders } from "test-utils";
import { Mock } from "vitest";
import {
  Settings,
  getSettings,
  saveSettings,
  getDefaultSettings,
} from "#/services/settings";
import Session from "#/services/session";
import { fetchAgents, fetchModels } from "#/services/options";
import SettingsModal from "./SettingsModal";

const i18nSpy = vi.spyOn(i18next, "changeLanguage");
const startNewSessionSpy = vi.spyOn(Session, "startNewSession");
vi.spyOn(Session, "isConnected").mockImplementation(() => true);

vi.mock("#/services/settings", async (importOriginal) => ({
  ...(await importOriginal<typeof import("#/services/settings")>()),
  getSettings: vi.fn().mockReturnValue({
    LLM_MODEL: "gpt-4o",
    AGENT: "CodeActAgent",
    LANGUAGE: "en",
    LLM_API_KEY: "sk-...",
    CONFIRMATION_MODE: false,
    SECURITY_ANALYZER: "",
  }),
  getDefaultSettings: vi.fn().mockReturnValue({
    LLM_MODEL: "gpt-4o",
    AGENT: "CodeActAgent",
    LANGUAGE: "en",
    LLM_API_KEY: "",
    CONFIRMATION_MODE: false,
    SECURITY_ANALYZER: "",
  }),
  settingsAreUpToDate: vi.fn().mockReturnValue(true),
  saveSettings: vi.fn(),
}));

vi.mock("#/services/options", async (importOriginal) => ({
  ...(await importOriginal<typeof import("#/services/options")>()),
  fetchModels: vi
    .fn()
    .mockResolvedValue(
      Promise.resolve([
        "gpt-4o",
        "gpt-4o-mini",
        "azure/ada",
        "cohere.command-r-v1:0",
      ]),
    ),
  fetchAgents: vi
    .fn()
    .mockResolvedValue(Promise.resolve(["agent1", "agent2", "agent3"])),
}));

// Helper function to assert that fetchModels was called
async function assertModelsAndAgentsFetched() {
  await waitFor(() => {
    expect(fetchAgents).toHaveBeenCalledTimes(1);
    expect(fetchModels).toHaveBeenCalledTimes(1);
  });
}

describe("SettingsModal", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch existing agents and models from the API", async () => {
    renderWithProviders(<SettingsModal isOpen onOpenChange={vi.fn()} />);

    assertModelsAndAgentsFetched();
  });

  it("should close the modal when the close button is clicked", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    await act(async () =>
      renderWithProviders(<SettingsModal isOpen onOpenChange={onOpenChange} />),
    );

    const cancelButton = screen.getByRole("button", {
      name: /MODAL_CLOSE_BUTTON_LABEL/i, // i18n key
    });

    await user.click(cancelButton);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("should disabled the save button if the settings contain a missing value", async () => {
    const onOpenChangeMock = vi.fn();
    (getSettings as Mock).mockReturnValueOnce({
      LLM_MODEL: "",
    });
    await act(async () =>
      renderWithProviders(
        <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
      ),
    );

    const saveButton = screen.getByRole("button", { name: /save/i });

    expect(saveButton).toBeDisabled();
  });

  describe("onHandleSave", () => {
    const initialSettings: Partial<Settings> = {
      LLM_MODEL: "gpt-4o",
      AGENT: "CodeActAgent",
      LANGUAGE: "en",
      LLM_API_KEY: "sk-...",
      SECURITY_ANALYZER: "",
      CONFIRMATION_MODE: false,
    };

    it("should save the settings", async () => {
      const user = userEvent.setup();
      const onOpenChangeMock = vi.fn();
      renderWithProviders(
        <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
      );

      // Use the helper function to assert models were fetched
      await assertModelsAndAgentsFetched();

      const saveButton = screen.getByRole("button", { name: /save/i });
      const providerInput = screen.getByRole("combobox", {
        name: "LLM Provider",
      });
      const modelInput = screen.getByRole("combobox", { name: "LLM Model" });

      await user.click(providerInput);
      const azure = screen.getByText("Azure");
      await user.click(azure);

      await user.click(modelInput);
      const model3 = screen.getByText("ada");
      await user.click(model3);

      await user.click(saveButton);

      expect(saveSettings).toHaveBeenCalledWith({
        ...initialSettings,
        LLM_MODEL: "azure/ada",
      });
    });

    it("should reinitialize agent", async () => {
      const user = userEvent.setup();
      const onOpenChangeMock = vi.fn();
      await act(async () =>
        renderWithProviders(
          <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
        ),
      );

      const saveButton = screen.getByRole("button", { name: /save/i });
      const providerInput = screen.getByRole("combobox", {
        name: "LLM Provider",
      });
      const modelInput = screen.getByRole("combobox", { name: "LLM Model" });

      await user.click(providerInput);
      const openai = screen.getByText("OpenAI");
      await user.click(openai);

      await user.click(modelInput);
      const model3 = screen.getByText("gpt-4o-mini");
      await user.click(model3);

      await user.click(saveButton);

      expect(startNewSessionSpy).toHaveBeenCalled();
    });

    it("should change the language", async () => {
      const user = userEvent.setup();
      const onOpenChangeMock = vi.fn();
      await act(async () =>
        renderWithProviders(
          <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
        ),
      );

      const saveButton = screen.getByRole("button", { name: /save/i });
      const languageInput = screen.getByRole("combobox", { name: "language" });

      await user.click(languageInput);
      const spanish = screen.getByText("Español");

      await user.click(spanish);
      await user.click(saveButton);

      expect(i18nSpy).toHaveBeenCalledWith("es");
    });

    it("should close the modal", async () => {
      const user = userEvent.setup();
      const onOpenChangeMock = vi.fn();
      (getSettings as Mock).mockReturnValueOnce({
        LLM_MODEL: "gpt-4o",
        LLM_API_KEY: "sk-...",
      });
      await act(async () =>
        renderWithProviders(
          <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
        ),
      );

      await waitFor(() => {
        expect(fetchModels).toHaveBeenCalledTimes(1);
      });

      const saveButton = screen.getByRole("button", { name: /save/i });
      const providerInput = screen.getByRole("combobox", {
        name: "LLM Provider",
      });
      const modelInput = screen.getByRole("combobox", { name: "LLM Model" });

      await user.click(providerInput);
      const cohere = screen.getByText("cohere");
      await user.click(cohere);

      await user.click(modelInput);
      const model3 = screen.getByText("command-r-v1:0");
      await user.click(model3);

      expect(saveButton).not.toBeDisabled();
      await user.click(saveButton);

      expect(onOpenChangeMock).toHaveBeenCalledWith(false);
    });
  });

  it("should reset settings to defaults when the 'reset to defaults' button is clicked", async () => {
    const user = userEvent.setup();
    const onOpenChangeMock = vi.fn();
    (getSettings as Mock).mockReturnValueOnce({
      LLM_MODEL: "gpt-4o",
      SECURITY_ANALYZER: "fakeanalyzer",
    });
    await act(async () =>
      renderWithProviders(
        <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
      ),
    );

    const resetButton = screen.getByRole("button", {
      name: /MODAL_RESET_BUTTON_LABEL/i,
    });
    const agentInput = screen.getByRole("combobox", { name: "agent" });

    await user.click(agentInput);
    const agent3 = screen.getByText("agent3");
    await user.click(agent3);
    expect(agentInput).toHaveValue("agent3");

    await user.click(resetButton);
    expect(getDefaultSettings).toHaveBeenCalled();

    expect(agentInput).toHaveValue("CodeActAgent"); // Agent value is reset to default from getDefaultSettings()
  });

  it.todo(
    "should display a loading spinner when fetching the models and agents",
  );
});
