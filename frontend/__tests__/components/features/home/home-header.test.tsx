import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { createRoutesStub } from "react-router";
import { setupStore } from "test-utils";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { HomeHeader } from "#/components/features/home/home-header";
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
          "HOME$LETS_START_BUILDING": "Let's start building",
          "HOME$LAUNCH_FROM_SCRATCH": "Launch from Scratch",
          "HOME$LOADING": "Loading...",
          "HOME$OPENHANDS_DESCRIPTION": "OpenHands is an AI software engineer",
          "HOME$NOT_SURE_HOW_TO_START": "Not sure how to start?",
          "HOME$READ_THIS": "Read this"
        };
        return translations[key] || key;
      },
      i18n: { language: "en" },
    }),
  };
});

const renderHomeHeader = () => {
  const RouterStub = createRoutesStub([
    {
      Component: HomeHeader,
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

describe("HomeHeader", () => {
  it("should create an empty conversation and redirect when pressing the launch from scratch button", async () => {
    const createConversationSpy = vi.spyOn(OpenHands, "createConversation");

    renderHomeHeader();

    const launchButton = screen.getByRole("button", {
      name: /Launch from Scratch/i,
    });
    await userEvent.click(launchButton);

    expect(createConversationSpy).toHaveBeenCalledExactlyOnceWith(
      undefined,
      undefined,
      undefined,
      [],
      undefined,
      undefined,
      undefined,
    );

    // expect to be redirected to /conversations/:conversationId
    await screen.findByTestId("conversation-screen");
  });

  it("should change the launch button text to 'Loading...' when creating a conversation", async () => {
    renderHomeHeader();

    const launchButton = screen.getByRole("button", {
      name: /Launch from Scratch/i,
    });
    await userEvent.click(launchButton);

    expect(launchButton).toHaveTextContent(/Loading.../i);
    expect(launchButton).toBeDisabled();
  });
});
