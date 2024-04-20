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

  it("should display the selected model", async () => {
    (fetchModels as Mock).mockResolvedValue(["model1", "model2"]);
    (getCurrentSettings as Mock).mockReturnValueOnce({
      LLM_MODEL: "model2",
    });

    await act(async () => render(<SettingsForm />));

    await waitFor(() => {
      expect(screen.getByText("model2")).toBeInTheDocument();
    });
  });

  it("should display the selected agent", async () => {
    (fetchAgents as Mock).mockResolvedValue(["agent1", "agent2"]);
    (getCurrentSettings as Mock).mockReturnValue({
      AGENT: "agent2",
    });

    await act(async () => render(<SettingsForm />));

    await waitFor(() => {
      expect(screen.getByText("agent2")).toBeInTheDocument();
    });
  });

  it.skip("should open a dropdown with the available models", async () => {
    (fetchModels as Mock).mockResolvedValue(["model1", "model2", "model3"]);

    render(<SettingsForm />);

    await waitFor(() => {
      expect(screen.getByText("model1")).toBeInTheDocument();
      expect(screen.queryByText("model2")).not.toBeInTheDocument();
      expect(screen.queryByText("model3")).not.toBeInTheDocument();
    });

    act(() => {
      userEvent.click(screen.getByText("model1"));
    });

    expect(screen.getByText("model2")).toBeInTheDocument();
    expect(screen.getByText("model3")).toBeInTheDocument();
  });
});
