import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { renderWithProviders } from "test-utils";
import AgentTaskState from "#/types/AgentTaskState";
import SettingsForm from "./SettingsForm";

const onModelChangeMock = vi.fn();
const onAgentChangeMock = vi.fn();
const onLanguageChangeMock = vi.fn();

const renderSettingsForm = (settings: Partial<Settings>) => {
  renderWithProviders(
    <SettingsForm
      settings={settings}
      models={["model1", "model2", "model3"]}
      agents={["agent1", "agent2", "agent3"]}
      onModelChange={onModelChangeMock}
      onAgentChange={onAgentChangeMock}
      onLanguageChange={onLanguageChangeMock}
    />,
  );
};

describe("SettingsForm", () => {
  it("should display the first values in the array by default", () => {
    renderSettingsForm({});

    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });

    expect(modelInput).toHaveValue("model1");
    expect(agentInput).toHaveValue("agent1");
    expect(languageInput).toHaveValue("English");
  });

  it("should display the existing values if it they are present", () => {
    renderSettingsForm({
      LLM_MODEL: "model2",
      AGENT: "agent2",
      LANGUAGE: "es",
    });

    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });

    expect(modelInput).toHaveValue("model2");
    expect(agentInput).toHaveValue("agent2");
    expect(languageInput).toHaveValue("Español");
  });

  it("should disable settings while task is running", () => {
    renderWithProviders(
      <SettingsForm
        settings={{}}
        models={["model1", "model2", "model3"]}
        agents={["agent1", "agent2", "agent3"]}
        onModelChange={onModelChangeMock}
        onAgentChange={onAgentChangeMock}
        onLanguageChange={onLanguageChangeMock}
      />,
      { preloadedState: { agent: { curTaskState: AgentTaskState.RUNNING } } },
    );
    const modelInput = screen.getByRole("combobox", { name: "model" });
    const agentInput = screen.getByRole("combobox", { name: "agent" });
    const languageInput = screen.getByRole("combobox", { name: "language" });

    expect(modelInput).toBeDisabled();
    expect(agentInput).toBeDisabled();
    expect(languageInput).toBeDisabled();
  });

  describe("onChange handlers", () => {
    it("should call the onModelChange handler when the model changes", () => {
      renderSettingsForm({});

      const modelInput = screen.getByRole("combobox", { name: "model" });
      act(() => {
        userEvent.click(modelInput);
      });

      const model3 = screen.getByText("model3");
      act(() => {
        userEvent.click(model3);
      });

      expect(onModelChangeMock).toHaveBeenCalledWith("model3");
    });

    it("should call the onAgentChange handler when the agent changes", () => {
      renderSettingsForm({});

      const agentInput = screen.getByRole("combobox", { name: "agent" });
      act(() => {
        userEvent.click(agentInput);
      });

      const agent3 = screen.getByText("agent3");
      act(() => {
        userEvent.click(agent3);
      });

      expect(onAgentChangeMock).toHaveBeenCalledWith("agent3");
    });

    it("should call the onLanguageChange handler when the language changes", () => {
      renderSettingsForm({});

      const languageInput = screen.getByRole("combobox", { name: "language" });
      act(() => {
        userEvent.click(languageInput);
      });

      const french = screen.getByText("Français");
      act(() => {
        userEvent.click(french);
      });

      expect(onLanguageChangeMock).toHaveBeenCalledWith("Français");
    });
  });
});
