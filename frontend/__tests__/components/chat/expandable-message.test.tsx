import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { ExpandableMessage } from "#/components/features/chat/expandable-message";
import OpenHands from "#/api/open-hands";

vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => key,
      i18n: {
        changeLanguage: () => new Promise(() => {}),
        language: "en",
        exists: () => true,
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

  const testTimestamp = "2025-03-21T10:00:00Z";

  it(`should display LocalFormat if timestamp is UtcFormat for`, async () => {
    const testTimestampLocalFormat = "2025-03-21T10:00:00";
    renderWithProviders(
      <ExpandableMessage
        message="Agent Message"
        type="thought"
        timestamp={testTimestampLocalFormat}
        sender="assistant"
      />,
    );

    const agent = "Agent";
    const date = new Date(`${testTimestampLocalFormat}Z`);
    const pad = (num: number): string => num.toString().padStart(2, "0");
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    const hour = pad(date.getHours());
    const minute = pad(date.getMinutes());
    const agentNameElement = await screen.findByText(agent);

    expect(agentNameElement.textContent?.trim()).toBe(agent);
    expect(
      await screen.findByText((content) =>
        content.includes(`${month}/${day} ${hour}:${minute}`),
      ),
    ).toBeInTheDocument();
  });

  it(`should display Agent if sender is assistant and agentName is undefind`, async () => {
    renderWithProviders(
      <ExpandableMessage
        message="Agent Message"
        type="thought"
        timestamp={testTimestamp}
        sender="assistant"
      />,
    );

    const agent = "Agent";
    const agentNameElement = await screen.findByText(agent);

    const date = new Date(testTimestamp);
    const pad = (num: number): string => num.toString().padStart(2, "0");
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    const hour = pad(date.getHours());
    const minute = pad(date.getMinutes());

    expect(agentNameElement.textContent?.trim()).toBe(agent);
    expect(
      await screen.findByText((content) =>
        content.includes(`${month}/${day} ${hour}:${minute}`),
      ),
    ).toBeInTheDocument();
  });

  it(`should display Agent if sender is assistant and timestamp is undefind`, async () => {
    renderWithProviders(
      <ExpandableMessage
        message="Agent Message"
        type="thought"
        sender="assistant"
      />,
    );

    const agent = "Agent";
    const agentNameElement = await screen.findByText(agent);

    expect(agentNameElement.textContent?.trim()).toBe(agent);
    expect(
      await screen.findByText((content) => content.includes("N/A")),
    ).toBeInTheDocument();
  });

  it("should display N/A if sender is assistant and timestamp is undefind", async () => {
    renderWithProviders(
      <ExpandableMessage
        message="Assistant Message"
        type="thought"
        sender="assistant"
      />,
    );
    expect(await screen.findByText("Agent")).toBeInTheDocument();
    expect(
      await screen.findByText((content) => content.trim() === "N/A"),
    ).toBeInTheDocument();
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
});
