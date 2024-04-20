import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import { Mock } from "vitest";
import userEvent from "@testing-library/user-event";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
  saveSettings,
} from "../../services/settingsService";
import SettingsForm from "./SettingsForm";

vi.mock("../../services/settingsService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../services/settingsService")>()),
  getCurrentSettings: vi.fn().mockReturnValue({}),
  saveSettings: vi.fn(),
  fetchModels: vi
    .fn()
    .mockResolvedValue(Promise.resolve(["model1", "model2", "model3"])),
  fetchAgents: vi
    .fn()
    .mockResolvedValue(Promise.resolve(["agent1", "agent2", "agent3"])),
}));

describe("SettingsForm", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch existing agents and models from the API", async () => {
    render(<SettingsForm />);

    await waitFor(() => {
      expect(fetchModels).toHaveBeenCalledTimes(1);
      expect(fetchAgents).toHaveBeenCalledTimes(1);
    });
  });

  it("should display the first values by default", async () => {
    await act(async () => render(<SettingsForm />));

    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });

    expect(modelInput).toHaveValue("model1");
    expect(agentInput).toHaveValue("agent1");
    expect(languageInput).toHaveValue("English");
  });

  it("should display the selected values if it they already exist", async () => {
    (getCurrentSettings as Mock).mockReturnValueOnce({
      LLM_MODEL: "model2",
      AGENT: "agent2",
      LANGUAGE: "es",
    });

    await act(async () => render(<SettingsForm />));

    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });

    expect(modelInput).toHaveValue("model2");
    expect(agentInput).toHaveValue("agent2");
    expect(languageInput).toHaveValue("Español");
  });

  it("should call saveSettings with the new values", async () => {
    await act(async () => render(<SettingsForm />));

    const modelInput = screen.getByRole("combobox", { name: "model" });

    act(() => {
      userEvent.click(modelInput);
    });

    const model3 = screen.getByText("model3");

    act(() => {
      userEvent.click(model3);
    });

    const saveButton = screen.getByTestId("save");

    act(() => {
      userEvent.click(saveButton);
    });

    expect(saveSettings).toHaveBeenCalledWith({
      LLM_MODEL: "model3",
    });
  });
});
