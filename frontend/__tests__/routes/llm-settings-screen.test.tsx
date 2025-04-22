import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it } from "vitest";
import LlmSettingsScreen from "#/routes/llm-settings-screen";

const renderLlmSettingsScreen = () => render(<LlmSettingsScreen />);

describe("Content", () => {
  describe("Basic form", () => {
    it("should render the basic form by default", async () => {
      renderLlmSettingsScreen();

      const basicFom = screen.getByTestId("llm-settings-form-basic");
      within(basicFom).getByTestId("llm-provider-input");
      within(basicFom).getByTestId("llm-model-input");
      within(basicFom).getByTestId("llm-api-key-input");
      within(basicFom).getByTestId("llm-api-key-help-anchor");
    });

    it.todo("should render the default values if non exist");
    it.todo("should render the existing settings values");
  });

  describe("Advanced form", () => {
    it("should render the advanced form if the switch is toggled", async () => {
      renderLlmSettingsScreen();

      const advancedSwitch = screen.getByTestId("advanced-settings-switch");
      const basicForm = screen.getByTestId("llm-settings-form-basic");

      expect(
        screen.queryByTestId("llm-settings-form-advanced"),
      ).not.toBeInTheDocument();
      expect(basicForm).toBeInTheDocument();

      await userEvent.click(advancedSwitch);

      expect(
        screen.queryByTestId("llm-settings-form-advanced"),
      ).toBeInTheDocument();
      expect(basicForm).not.toBeInTheDocument();

      const advancedForm = screen.getByTestId("llm-settings-form-advanced");
      within(advancedForm).getByTestId("llm-custom-model-input");
      within(advancedForm).getByTestId("base-url-input");
      within(advancedForm).getByTestId("llm-api-key-input");
      within(advancedForm).getByTestId("llm-api-key-help-anchor");
      within(advancedForm).getByTestId("agent-input");
      within(advancedForm).getByTestId("enable-confirmation-mode-switch");
      within(advancedForm).getByTestId("enable-memory-condenser-switch");

      await userEvent.click(advancedSwitch);
      expect(
        screen.queryByTestId("llm-settings-form-advanced"),
      ).not.toBeInTheDocument();
      expect(screen.getByTestId("llm-settings-form-basic")).toBeInTheDocument();
    });

    it.todo(
      "should render the advanced form if existings settings are advanced",
    );
  });
});

describe("Form submission", () => {
  it.todo("should submit the basic form with the correct values");
  it.todo("should submit the advanced form with the correct values");
  it.todo(
    "should disable the button if there are no changes in the basic form",
  );
  it.todo(
    "should disable the button if there are no changes in the advanced form",
  );
  it.todo("should disable the button when submitting changes");
});

describe.todo("Status toasts", () => {
  it.todo("should call displaySuccessToast when the settings are saved");
  it.todo("should call displayErrorToast when the settings are saved");
});
