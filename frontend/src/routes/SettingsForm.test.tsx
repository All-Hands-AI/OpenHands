import { render, screen, within } from "@testing-library/react";
import React from "react";
import { describe, it, expect } from "vitest";
import userEvent from "@testing-library/user-event";
import { SettingsForm } from "./SettingsForm";

vi.mock("react-router-dom", async (importActual) => ({
  ...(await importActual<typeof import("react-router-dom")>()),
  useFetcher: () => ({
    Form: ({ children }: { children: React.ReactNode }) => (
      <form data-testid="settings-form">{children}</form>
    ),
  }),
}));

describe("SettingsForm", () => {
  const settings = {
    LLM_MODEL: "openai/gpt-4o",
    AGENT: "CodeActAgent",
  };

  const models = ["openai/gpt-4o", "openai/gpt-3.5-turbo"];
  const agents = ["CodeActAgent", "MonologueAgent", "DummyAgent"];

  it("should render the form", () => {
    render(<SettingsForm settings={settings} models={[]} agents={[]} />);

    const form = screen.getByTestId("settings-form");
    within(form).getByTestId("custom-model-toggle");
    within(form).getByTestId("model-selector");
    within(form).getByTestId("api-key-input");
    within(form).getByTestId("agent-selector");
    within(form).getByTestId("security-analyzer-selector");
    within(form).getByTestId("confirmation-mode-toggle");
  });

  describe("Models", () => {
    it("should display the available models", async () => {
      const user = userEvent.setup();
      render(<SettingsForm settings={settings} models={models} agents={[]} />);
      const form = screen.getByTestId("settings-form");

      const model = within(form).getByLabelText("Model");
      await user.click(model);

      screen.getByText("gpt-4o");
      screen.getByText("gpt-3.5-turbo");
    });

    it("should display the selected model", () => {
      render(<SettingsForm settings={settings} models={[]} agents={[]} />);
      const form = screen.getByTestId("settings-form");

      const modelSelector = within(form).getByTestId("model-selector");
      const model = within(modelSelector).getByTestId("model-id");
      expect(model).toHaveTextContent("openai/gpt-4o");
    });
  });

  describe("Agents", () => {
    it("should display the available agents", async () => {
      const user = userEvent.setup();
      render(<SettingsForm settings={settings} models={[]} agents={agents} />);
      const form = screen.getByTestId("settings-form");

      const agent = within(form).getByLabelText("Agent");
      await user.click(agent);

      screen.getByText("CodeActAgent");
      screen.getByText("MonologueAgent");
      screen.getByText("DummyAgent");
    });

    it("should display the selected agent", () => {
      render(<SettingsForm settings={settings} models={[]} agents={agents} />);
      const form = screen.getByTestId("settings-form");

      const agentSelector = within(form).getByTestId("agent-selector");
      const input = within(agentSelector).getByTestId("agent-input");
      expect(input).toHaveValue("CodeActAgent");
    });
  });
});
