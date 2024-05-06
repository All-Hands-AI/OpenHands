import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import i18next from "i18next";
import React from "react";
import { renderWithProviders } from "test-utils";
import { Mock } from "vitest";
import toast from "#/utils/toast";
import { Settings, getSettings, saveSettings } from "#/services/settings";
import { initializeAgent } from "#/services/agent";
import { fetchAgents, fetchModels } from "#/api";
import SettingsModal from "./SettingsModal";

const toastSpy = vi.spyOn(toast, "settingsChanged");
const i18nSpy = vi.spyOn(i18next, "changeLanguage");

vi.mock("#/services/settings", async (importOriginal) => ({
  ...(await importOriginal<typeof import("#/services/settings")>()),
  getSettings: vi.fn().mockReturnValue({
    LLM_MODEL: "gpt-3.5-turbo",
    AGENT: "MonologueAgent",
    LANGUAGE: "en",
  }),
  saveSettings: vi.fn(),
}));

vi.mock("#/services/agent", async () => ({
  initializeAgent: vi.fn(),
}));

vi.mock("#/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("#/api")>()),
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

  it("should close the modal when the cancel button is clicked", async () => {
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

  it("should disable the save button if the settings are the same as the initial settings", async () => {
    await act(async () =>
      renderWithProviders(<SettingsModal isOpen onOpenChange={vi.fn()} />),
    );

    const saveButton = screen.getByRole("button", { name: /save/i });

    expect(saveButton).toBeDisabled();
  });

  it("should disabled the save button if the settings contain a missing value", () => {
    const onOpenChangeMock = vi.fn();
    (getSettings as Mock).mockReturnValueOnce({
      LLM_MODEL: "gpt-3.5-turbo",
      AGENT: "",
    });
    renderWithProviders(
      <SettingsModal isOpen onOpenChange={onOpenChangeMock} />,
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

      expect(initializeAgent).toHaveBeenCalledWith({
        ...initialSettings,
        LLM_MODEL: "model3",
        LLM_API_KEY: "", // reset after model change
      });
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

  it.todo("should reset setting changes when the cancel button is clicked");

  it.todo(
    "should display a loading spinner when fetching the models and agents",
  );
});
