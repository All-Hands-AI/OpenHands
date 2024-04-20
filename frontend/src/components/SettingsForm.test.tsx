import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import { Mock } from "vitest";
import userEvent from "@testing-library/user-event";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
} from "../services/settingsService";
import SettingsForm from "./SettingsForm";

vi.mock("../services/settingsService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../services/settingsService")>()),
  getCurrentSettings: vi.fn().mockReturnValue({}),
  fetchModels: vi.fn().mockResolvedValue(Promise.resolve([])),
  fetchAgents: vi.fn().mockResolvedValue(Promise.resolve([])),
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

  it("should display the first model by default", async () => {
    (fetchModels as Mock).mockResolvedValue(["model1", "model2"]);

    await act(async () => render(<SettingsForm />));

    expect(screen.getByRole("combobox", { name: "model" })).toHaveValue(
      "model1",
    );
  });

  it("should display the first agent by default", async () => {
    (fetchAgents as Mock).mockResolvedValue(["agent1", "agent2"]);

    await act(async () => render(<SettingsForm />));

    expect(screen.getByRole("combobox", { name: "agent" })).toHaveValue(
      "agent1",
    );
  });

  it("should display the model if it already exists in the settings", async () => {
    (fetchModels as Mock).mockResolvedValue(["model1", "model2"]);
    (getCurrentSettings as Mock).mockReturnValueOnce({
      LLM_MODEL: "model2",
    });

    await act(async () => render(<SettingsForm />));

    const input = screen.getByRole("combobox", { name: "model" });
    expect(input).toHaveValue("model2");
  });

  it("should display the agent if it already exists in the settings", async () => {
    (fetchAgents as Mock).mockResolvedValue(["agent1", "agent2"]);
    (getCurrentSettings as Mock).mockReturnValue({
      AGENT: "agent2",
    });

    await act(async () => render(<SettingsForm />));

    const input = screen.getByRole("combobox", { name: "agent" });
    expect(input).toHaveValue("agent2");
  });

  it("should open a dropdown with the available models", async () => {
    (fetchModels as Mock).mockResolvedValue(["model1", "model2", "model3"]);

    await act(async () => render(<SettingsForm />));

    const input = screen.getByRole("combobox", { name: "model" });

    act(() => {
      userEvent.click(input);
    });

    expect(screen.getByText("model2")).toBeInTheDocument();
    expect(screen.getByText("model3")).toBeInTheDocument();
  });

  it("should open a dropdown with the available agents", async () => {
    (fetchAgents as Mock).mockResolvedValue(["agent1", "agent2", "agent3"]);

    await act(async () => render(<SettingsForm />));

    const input = screen.getByRole("combobox", { name: "agent" });

    act(() => {
      userEvent.click(input);
    });

    expect(screen.getByText("agent2")).toBeInTheDocument();
    expect(screen.getByText("agent3")).toBeInTheDocument();
  });
});
