import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import i18next from "i18next";
import React from "react";
import { renderWithProviders } from "test-utils";
import { Mock } from "vitest";
import toast from "#/utils/toast";
import {
  Settings,
  getSettings,
  saveSettings,
  getDefaultSettings,
} from "#/services/settings";
import Session from "#/services/session";
import { fetchAgents, fetchModels } from "#/services/options";
import SettingsModal from "./SettingsModal";

const toastSpy = vi.spyOn(toast, "settingsChanged");
const i18nSpy = vi.spyOn(i18next, "changeLanguage");
const startNewSessionSpy = vi.spyOn(Session, "startNewSession");
vi.spyOn(Session, "isConnected").mockImplementation(() => true);

vi.mock("#/services/settings", async (importOriginal) => ({
  ...(await importOriginal<typeof import("#/services/settings")>()),
  getSettings: vi.fn().mockReturnValue({
    LLM_MODEL: "gpt-3.5-turbo",
    AGENT: "MonologueAgent",
    LANGUAGE: "en",
  }),
  getDefaultSettings: vi.fn().mockReturnValue({
    LLM_MODEL: "gpt-3.5-turbo",
    AGENT: "CodeActAgent",
    LANGUAGE: "en",
    LLM_API_KEY: "",
  }),
  settingsAreUpToDate: vi.fn().mockReturnValue(true),
  saveSettings: vi.fn(),
}));

vi.mock("#/services/options", async (importOriginal) => ({
  ...(await importOriginal<typeof import("#/services/options")>()),
  fetchModels: vi
    .fn()
    .mockResolvedValue(Promise.resolve(["model1", "model2", "model3"])),
  fetchAgents: vi
    .fn()
    .mockResolvedValue(Promise.resolve(["agent1", "agent2", "agent3"])),
}));

describe("SettingsModal", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch existing agents and models from the API", async () => {
    renderWithProviders(<SettingsModal isOpen onOpenChange={vi.fn()} />);

    await waitFor(() => {
      expect(fetchModels).toHaveBeenCalledTimes(1);
      expect(fetchAgents).toHaveBeenCalledTimes(1);
    });
  });

  it("should close the modal when the close button is clicked", async () => {
    const onOpenChange = vi.fn();
    await act(async () =>
      renderWithProviders(<SettingsModal isOpen onOpenChange={onOpenChange} />),
    );

    const cancelButton = screen.getByRole("button", {
      name: /MODAL_CLOSE_BUTTON_LABEL/i, // i18n key
    });

    act(() => {
      userEvent.click(cancelButton);
    });

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("should disabled the save button if the settings contain a missing value", async () => {
    const onOpenChangeMock = vi.fn();
    (getSettings as Mock).mockReturnValueOnce({
      LLM_MODEL: "gpt-3.5-turbo",
      AGENT: "",
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
    const initialSettings: Settings = {
      LLM_MODEL: "gpt-3.5-turbo",
      AGENT: "MonologueAgent",
      LANGUAGE: "en",
      LLM_API_KEY: "sk-...",
    };

    it("should save the settings", async () => {
      const onOpenChangeMock = vi.fn();
      await act(async () =>
        renderWithProviders(
          <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
        ),
      );

      const saveButton = screen.getByRole("button", { name: /save/i });
      const modelInput = screen.getByRole("combobox", { name: "model" });

      act(() => {
        userEvent.click(modelInput);
      });

      const model3 = screen.getByText("model3");

      act(() => {
        userEvent.click(model3);
      });

      act(() => {
        userEvent.click(saveButton);
      });

      expect(saveSettings).toHaveBeenCalledWith({
        ...initialSettings,
        LLM_MODEL: "model3",
        LLM_API_KEY: "", // reset after model change
      });
    });

    it("should reinitialize agent", async () => {
      const onOpenChangeMock = vi.fn();
      await act(async () =>
        renderWithProviders(
          <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
        ),
      );

      const saveButton = screen.getByRole("button", { name: /save/i });
      const modelInput = screen.getByRole("combobox", { name: "model" });

      act(() => {
        userEvent.click(modelInput);
      });

      const model3 = screen.getByText("model3");

      act(() => {
        userEvent.click(model3);
      });

      act(() => {
        userEvent.click(saveButton);
      });

      expect(startNewSessionSpy).toHaveBeenCalled();
    });

    it("should display a toast for every change", async () => {
      const onOpenChangeMock = vi.fn();
      await act(async () =>
        renderWithProviders(
          <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
        ),
      );

      const saveButton = screen.getByRole("button", { name: /save/i });
      const modelInput = screen.getByRole("combobox", { name: "model" });

      act(() => {
        userEvent.click(modelInput);
      });

      const model3 = screen.getByText("model3");

      act(() => {
        userEvent.click(model3);
      });

      act(() => {
        userEvent.click(saveButton);
      });

      expect(toastSpy).toHaveBeenCalledTimes(2);
    });

    it("should change the language", async () => {
      const onOpenChangeMock = vi.fn();
      await act(async () =>
        renderWithProviders(
          <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
        ),
      );

      const saveButton = screen.getByRole("button", { name: /save/i });
      const languageInput = screen.getByRole("combobox", { name: "language" });

      act(() => {
        userEvent.click(languageInput);
      });

      const spanish = screen.getByText("Español");

      act(() => {
        userEvent.click(spanish);
      });

      act(() => {
        userEvent.click(saveButton);
      });

      expect(i18nSpy).toHaveBeenCalledWith("es");
    });

    it("should close the modal", async () => {
      const onOpenChangeMock = vi.fn();
      await act(async () =>
        renderWithProviders(
          <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
        ),
      );

      const saveButton = screen.getByRole("button", { name: /save/i });
      const modelInput = screen.getByRole("combobox", { name: "model" });

      act(() => {
        userEvent.click(modelInput);
      });

      const model3 = screen.getByText("model3");

      act(() => {
        userEvent.click(model3);
      });

      act(() => {
        userEvent.click(saveButton);
      });

      expect(onOpenChangeMock).toHaveBeenCalledWith(false);
    });
  });

  it("should reset settings to defaults when the 'reset to defaults' button is clicked", async () => {
    const onOpenChangeMock = vi.fn();
    await act(async () =>
      renderWithProviders(
        <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
      ),
    );

    const resetButton = screen.getByRole("button", {
      name: /MODAL_RESET_BUTTON_LABEL/i,
    });
    const agentInput = screen.getByRole("combobox", { name: "agent" });

    act(() => {
      userEvent.click(agentInput);
    });
    const agent3 = screen.getByText("agent3");
    act(() => {
      userEvent.click(agent3);
    });
    expect(agentInput).toHaveValue("agent3");

    act(() => {
      userEvent.click(resetButton);
    });
    expect(getDefaultSettings).toHaveBeenCalled();

    expect(agentInput).toHaveValue("CodeActAgent"); // Agent value is reset to default from getDefaultSettings()
  });

  it.todo(
    "should display a loading spinner when fetching the models and agents",
  );
});
