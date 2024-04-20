import React from "react";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { Mock } from "vitest";
import userEvent from "@testing-library/user-event";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
} from "../../services/settingsService";
import SettingsForm from "./SettingsForm";
import { AvailableLanguages } from "../../i18n";

vi.mock("../../services/settingsService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../services/settingsService")>()),
  getCurrentSettings: vi.fn().mockReturnValue({}),
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

  it("should retrieve current settings when mounted", async () => {
    await act(async () => render(<SettingsForm />));
    expect(getCurrentSettings).toHaveBeenCalledTimes(1);
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

    expect(modelInput).toHaveValue("model1");
    expect(agentInput).toHaveValue("agent1");
  });

  it("should display the selected values if it they already exist", async () => {
    (getCurrentSettings as Mock).mockReturnValueOnce({
      LLM_MODEL: "model2",
      AGENT: "agent2",
    });

    await act(async () => render(<SettingsForm />));

    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });

    expect(modelInput).toHaveValue("model2");
    expect(agentInput).toHaveValue("agent2");
  });

  it("should display the language selector", async () => {
    await act(async () => render(<SettingsForm />));

    const languageInput = screen.getByRole("button", { name: /language/i });

    expect(languageInput).toBeInTheDocument();
    within(languageInput).getByText(/english/i);

    act(() => {
      userEvent.click(languageInput);
    });

    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(AvailableLanguages.length);
  });
});
