import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { createRoutesStub } from "react-router";
import { setupStore } from "test-utils";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { NewConversation } from "#/components/features/home/new-conversation";
import OpenHands from "#/api/open-hands";

// Mock the translation function
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        // Return a mock translation for the test
        const translations: Record<string, string> = {
          COMMON$START_FROM_SCRATCH: "Start from Scratch",
          HOME$NEW_PROJECT_DESCRIPTION: "Create a new project from scratch",
          COMMON$NEW_CONVERSATION: "New Conversation",
          HOME$LOADING: "Loading...",
        };
        return translations[key] || key;
      },
      i18n: { language: "en" },
    }),
  };
});

const renderNewConversation = () => {
  const RouterStub = createRoutesStub([
    {
      Component: NewConversation,
      path: "/",
    },
    {
      Component: () => <div data-testid="conversation-screen" />,
      path: "/conversations/:conversationId",
    },
  ]);

  return render(<RouterStub />, {
    wrapper: ({ children }) => (
      <Provider store={setupStore()}>
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      </Provider>
    ),
  });
};

describe("NewConversation", () => {
  it("should create an empty conversation and redirect when pressing the launch from scratch button", async () => {
    const createConversationSpy = vi.spyOn(OpenHands, "createConversation");

    renderNewConversation();

    const launchButton = screen.getByTestId("launch-new-conversation-button");
    await userEvent.click(launchButton);

    expect(createConversationSpy).toHaveBeenCalledExactlyOnceWith(
      undefined,
      undefined,
      undefined,
      undefined,
      undefined,
      undefined,
      undefined,
    );

    // expect to be redirected to /conversations/:conversationId
    await screen.findByTestId("conversation-screen");
  });

  it("should change the launch button text to 'Loading...' when creating a conversation", async () => {
    renderNewConversation();

    const launchButton = screen.getByTestId("launch-new-conversation-button");
    await userEvent.click(launchButton);

    expect(launchButton).toHaveTextContent(/Loading.../i);
    expect(launchButton).toBeDisabled();
  });
});
