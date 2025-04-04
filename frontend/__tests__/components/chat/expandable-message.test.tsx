import { describe, expect, it, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { ExpandableMessage } from "#/components/features/chat/expandable-message";
import OpenHands from "#/api/open-hands";

vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        // Return a different value for translation keys to verify translation is happening
        if (key === "STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR") {
          return "The request failed with an internal server error.";
        }
        if (key === "STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR_MESSAGE") {
          return "Something went wrong with the AI provider. This could be due to server overload or temporary issues. Please try again later.";
        }
        return key;
      },
      i18n: {
        changeLanguage: () => new Promise(() => {}),
        language: "en",
        exists: (key: string) => {
          // Return true for our test translation keys
          return key === "STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR" || 
                 key === "STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR_MESSAGE" || 
                 true;
        },
      },
    }),
  };
});

describe("ExpandableMessage", () => {
  it("should render with neutral border for non-action messages", () => {
    renderWithProviders(<ExpandableMessage message="Hello" type="thought" />);
    const element = screen.getByText("Hello");
    const container = element.closest(
      "div.flex.gap-2.items-center.justify-start",
    );
    expect(container).toHaveClass("border-neutral-300");
    expect(screen.queryByTestId("status-icon")).not.toBeInTheDocument();
  });

  it("should render with neutral border for error messages", () => {
    renderWithProviders(
      <ExpandableMessage message="Error occurred" type="error" />,
    );
    const element = screen.getByText("Error occurred");
    const container = element.closest(
      "div.flex.gap-2.items-center.justify-start",
    );
    expect(container).toHaveClass("border-danger");
    expect(screen.queryByTestId("status-icon")).not.toBeInTheDocument();
  });

  it("should render with success icon for successful action messages", () => {
    renderWithProviders(
      <ExpandableMessage
        id="OBSERVATION_MESSAGE$RUN"
        message="Command executed successfully"
        type="action"
        success
      />,
    );
    const element = screen.getByText("OBSERVATION_MESSAGE$RUN");
    const container = element.closest(
      "div.flex.gap-2.items-center.justify-start",
    );
    expect(container).toHaveClass("border-neutral-300");
    const icon = screen.getByTestId("status-icon");
    expect(icon).toHaveClass("fill-success");
  });

  it("should render with error icon for failed action messages", () => {
    renderWithProviders(
      <ExpandableMessage
        id="OBSERVATION_MESSAGE$RUN"
        message="Command failed"
        type="action"
        success={false}
      />,
    );
    const element = screen.getByText("OBSERVATION_MESSAGE$RUN");
    const container = element.closest(
      "div.flex.gap-2.items-center.justify-start",
    );
    expect(container).toHaveClass("border-neutral-300");
    const icon = screen.getByTestId("status-icon");
    expect(icon).toHaveClass("fill-danger");
  });

  it("should render with neutral border and no icon for action messages without success prop", () => {
    renderWithProviders(
      <ExpandableMessage
        id="OBSERVATION_MESSAGE$RUN"
        message="Running command"
        type="action"
      />,
    );
    const element = screen.getByText("OBSERVATION_MESSAGE$RUN");
    const container = element.closest(
      "div.flex.gap-2.items-center.justify-start",
    );
    expect(container).toHaveClass("border-neutral-300");
    expect(screen.queryByTestId("status-icon")).not.toBeInTheDocument();
  });

  it("should render the out of credits message when the user is out of credits", async () => {
    const getConfigSpy = vi.spyOn(OpenHands, "getConfig");
    // @ts-expect-error - We only care about the APP_MODE and FEATURE_FLAGS fields
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      FEATURE_FLAGS: {
        ENABLE_BILLING: true,
        HIDE_LLM_SETTINGS: false,
      },
    });
    const RouterStub = createRoutesStub([
      {
        Component: () => (
          <ExpandableMessage
            id="STATUS$ERROR_LLM_OUT_OF_CREDITS"
            message=""
            type=""
          />
        ),
        path: "/",
      },
    ]);

    renderWithProviders(<RouterStub />);
    await screen.findByTestId("out-of-credits");
  });
  
  it("should properly handle translation keys in message content", () => {
    renderWithProviders(
      <ExpandableMessage
        id="STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR"
        message="STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR"
        type="error"
      />,
    );
    
    // Should show the translated headline, not the raw key
    expect(screen.getByText("The request failed with an internal server error.")).toBeInTheDocument();
    
    // The raw key should not be visible
    expect(screen.queryByText("STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR")).not.toBeInTheDocument();
    
    // Since we're using the original button rendering logic from main branch,
    // we need to update the test to expect a button to be present
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });
  
  it("should properly handle the more descriptive error message", () => {
    renderWithProviders(
      <ExpandableMessage
        id="STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR"
        message="STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR_MESSAGE"
        type="error"
      />,
    );

    // Should show the translated headline from the id
    expect(screen.getByText("The request failed with an internal server error.")).toBeInTheDocument();

    // The raw key should not be visible
    expect(screen.queryByText("STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR_MESSAGE")).not.toBeInTheDocument();
  });
});
