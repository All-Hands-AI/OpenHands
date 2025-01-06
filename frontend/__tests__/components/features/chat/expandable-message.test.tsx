import { test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ExpandableMessage } from "#/components/features/chat/expandable-message";
import { I18nextProvider } from "react-i18next";
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// Initialize i18n for testing
i18n.use(initReactI18next).init({
  lng: "en",
  resources: {
    en: {
      translation: {
        "ACTION_MESSAGE$RUN": "this action has not been executed",
      },
    },
  },
});

test("should show only the headline for unexecuted actions", () => {
  render(
    <I18nextProvider i18n={i18n}>
      <ExpandableMessage
        type="action"
        id="ACTION_MESSAGE$RUN"
        message="Command:\n`ls -l`"
        success={undefined}
      />
    </I18nextProvider>
  );

  // The headline should be visible
  const headline = screen.getByText("this action has not been executed");
  expect(headline).toBeInTheDocument();
  expect(headline).toHaveClass("font-bold");

  // The command details should not be visible
  const details = screen.queryByText(/Command:/, { exact: false });
  expect(details).not.toBeInTheDocument();
});

test("should show only the details for completed successful actions", () => {
  render(
    <I18nextProvider i18n={i18n}>
      <ExpandableMessage
        type="action"
        id="ACTION_MESSAGE$RUN"
        message="Command executed successfully"
        success={true}
      />
    </I18nextProvider>
  );

  // The command details should be visible
  const details = screen.getByText("Command executed successfully");
  expect(details).toBeInTheDocument();

  // The success icon should be visible
  const statusIcon = screen.getByTestId("status-icon");
  expect(statusIcon).toHaveClass("fill-success");

  // The headline should not be visible
  const headline = screen.queryByText("this action has not been executed");
  expect(headline).not.toBeInTheDocument();
});

test("should show only the details for completed failed actions", () => {
  render(
    <I18nextProvider i18n={i18n}>
      <ExpandableMessage
        type="action"
        id="ACTION_MESSAGE$RUN"
        message="Command failed"
        success={false}
      />
    </I18nextProvider>
  );

  // The command details should be visible
  const details = screen.getByText("Command failed");
  expect(details).toBeInTheDocument();

  // The error icon should be visible
  const statusIcon = screen.getByTestId("status-icon");
  expect(statusIcon).toHaveClass("fill-danger");

  // The headline should not be visible
  const headline = screen.queryByText("this action has not been executed");
  expect(headline).not.toBeInTheDocument();
});
