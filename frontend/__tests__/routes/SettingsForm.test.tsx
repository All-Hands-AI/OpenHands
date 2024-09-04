import { render, screen, within } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { SettingsForm } from "../../src/routes/settings-form";

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
    CUSTOM_LLM_MODEL: "",
    USING_CUSTOM_MODEL: false,
    LLM_API_KEY: "",
  };

  const models = ["openai/gpt-4o", "openai/gpt-3.5-turbo"];
  const agents = ["CodeActAgent", "MonologueAgent", "DummyAgent"];

  it("should render the form", () => {
    const onClose = vi.fn();
    render(
      <SettingsForm
        settings={settings}
        models={[]}
        agents={[]}
        onClose={onClose}
      />,
    );

    const form = screen.getByTestId("settings-form");
    within(form).getByTestId("custom-model-toggle");
    within(form).getByTestId("model-selector");
    within(form).getByTestId("api-key-input");
    within(form).getByTestId("agent-selector");
  });

  it("should call onClose when the close button is clicked", async () => {
    const onClose = vi.fn();
    render(
      <SettingsForm
        settings={settings}
        models={[]}
        agents={[]}
        onClose={onClose}
      />,
    );
    const form = screen.getByTestId("settings-form");

    const closeButton = within(form).getByTestId("close-button");
    await userEvent.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });

  describe("Models", () => {
    it("should display the available models", async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();
      render(
        <SettingsForm
          settings={settings}
          models={models}
          agents={[]}
          onClose={onClose}
        />,
      );
      const form = screen.getByTestId("settings-form");

      const model = within(form).getByLabelText("Model");
      await user.click(model);

      screen.getByText("gpt-4o");
      screen.getByText("gpt-3.5-turbo");
    });

    it("should display the selected model", () => {
      const onClose = vi.fn();
      render(
        <SettingsForm
          settings={settings}
          models={[]}
          agents={[]}
          onClose={onClose}
        />,
      );
      const form = screen.getByTestId("settings-form");

      const modelSelector = within(form).getByTestId("model-selector");
      const model = within(modelSelector).getByTestId("model-id");
      expect(model).toHaveTextContent("openai/gpt-4o");
    });

    it("should display the custom model input when the custom model toggle is enabled", async () => {
      const onClose = vi.fn();
      render(
        <SettingsForm
          settings={{ ...settings, USING_CUSTOM_MODEL: true }}
          models={[]}
          agents={[]}
          onClose={onClose}
        />,
      );
      const form = screen.getByTestId("settings-form");

      const customModelInput = within(form).getByTestId("custom-model-input");
      expect(customModelInput).toBeInTheDocument();
    });
  });

  describe("Agents", () => {
    it("should display the available agents", async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();
      render(
        <SettingsForm
          settings={settings}
          models={[]}
          agents={agents}
          onClose={onClose}
        />,
      );
      const form = screen.getByTestId("settings-form");

      const agent = within(form).getByLabelText("Agent");
      await user.click(agent);

      screen.getByText("CodeActAgent");
      screen.getByText("MonologueAgent");
      screen.getByText("DummyAgent");
    });

    it("should display the selected agent", () => {
      const onClose = vi.fn();
      render(
        <SettingsForm
          settings={settings}
          models={[]}
          agents={agents}
          onClose={onClose}
        />,
      );
      const form = screen.getByTestId("settings-form");

      const agentSelector = within(form).getByTestId("agent-selector");
      const input = within(agentSelector).getByTestId("agent-input");
      expect(input).toHaveValue("CodeActAgent");
    });
  });
});
