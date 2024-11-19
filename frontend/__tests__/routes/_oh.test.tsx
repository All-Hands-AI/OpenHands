import { describe, expect, it, vi } from "vitest";
import { createRemixStub } from "@remix-run/testing";
import { screen, waitFor, within } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import userEvent from "@testing-library/user-event";
import MainApp from "#/routes/_oh";
import { getSettings } from "#/services/settings";
import * as CaptureConsent from "#/utils/handle-capture-consent";
import { clientAction } from "#/routes/set-consent";

describe("frontend/routes/_oh", () => {
  it("should render", async () => {
    const RemixStub = createRemixStub([
      { loader: () => ({}), Component: MainApp, path: "/" },
    ]);

    renderWithProviders(<RemixStub />);
    await screen.findByTestId("root-layout");
  });

  it("should render the AI config modal if the user is authed", async () => {
    vi.mock("#/utils/user-is-authenticated", () => ({
      userIsAuthenticated: vi.fn().mockReturnValue(true),
    }));

    const RemixStub = createRemixStub([
      {
        loader: () => ({
          settings: getSettings(),
        }),
        Component: MainApp,
        path: "/",
      },
    ]);

    renderWithProviders(<RemixStub />);
    await screen.findByTestId("ai-config-modal");
  });

  it("should render the AI config modal if settings are not up-to-date", async () => {
    vi.mock("#/services/settings", async (importOriginal) => ({
      ...(await importOriginal<typeof import("#/services/settings")>()),
      settingsAreUpToDate: vi.fn().mockReturnValue(false),
    }));

    vi.mock("#/utils/user-is-authenticated", () => ({
      userIsAuthenticated: vi.fn().mockReturnValue(true),
    }));

    const RemixStub = createRemixStub([
      {
        loader: () => ({
          settingsIsUpdated: false,
          settings: getSettings(),
        }),
        Component: MainApp,
        path: "/",
      },
      {
        // @ts-expect-error - clientAction's are not type-compatible with action
        action: clientAction,
        path: "/set-consent",
      },
    ]);

    renderWithProviders(<RemixStub />);
    await screen.findByTestId("ai-config-modal");
  });

  it("should clear the token key if the settings are not up-to-date", async () => {
    localStorage.setItem("token", "test-token");

    vi.mock("#/utils/user-is-authenticated", () => ({
      userIsAuthenticated: vi.fn().mockReturnValue(true),
    }));

    const RemixStub = createRemixStub([
      {
        loader: () => {
          localStorage.removeItem("token");
          return {
            settingsIsUpdated: false,
            settings: getSettings(),
          };
        },
        Component: MainApp,
        path: "/",
      },
    ]);

    renderWithProviders(<RemixStub />);
    expect(localStorage.getItem("token")).toBeNull();
  });

  it.fails("should capture the user's consent", async () => {
    const user = userEvent.setup();
    const handleCaptureConsentSpy = vi.spyOn(
      CaptureConsent,
      "handleCaptureConsent",
    );

    vi.mock("#/utils/user-is-authenticated", () => ({
      userIsAuthenticated: vi.fn().mockReturnValue(true),
    }));

    const RemixStub = createRemixStub([
      {
        loader: () => {
          const analyticsConsent = localStorage.getItem("analytics-consent");
          const userConsents = analyticsConsent === "true";

          CaptureConsent.handleCaptureConsent(userConsents);

          return {
            settings: getSettings(),
          };
        },
        Component: MainApp,
        path: "/",
      },
    ]);

    renderWithProviders(<RemixStub />);

    // The user has not consented to tracking
    const consentForm = await screen.findByTestId("user-capture-consent-form");
    expect(handleCaptureConsentSpy).not.toHaveBeenCalled();

    const submitButton = within(consentForm).getByRole("button", {
      name: /confirm preferences/i,
    });
    await user.click(submitButton);

    // The user has now consented to tracking
    expect(handleCaptureConsentSpy).toHaveBeenCalledWith(true);
  });

  it("should not render the user consent form if the user has already made a decision", async () => {
    const RemixStub = createRemixStub([
      {
        loader: () => ({
          analyticsConsent: "true",
          settings: getSettings(),
        }),
        Component: MainApp,
        path: "/",
      },
    ]);

    renderWithProviders(<RemixStub />);

    await waitFor(() => {
      expect(
        screen.queryByTestId("user-capture-consent-form"),
      ).not.toBeInTheDocument();
    });
  });

  it("should render a new project button if a token is set", async () => {
    localStorage.setItem("token", "test-token");

    const RemixStub = createRemixStub([
      {
        loader: () => ({
          token: localStorage.getItem("token"),
          settings: getSettings(),
        }),
        Component: MainApp,
        path: "/",
      },
    ]);

    renderWithProviders(<RemixStub />);

    await screen.findByTestId("new-project-button");
  });

  it.todo("should update the i18n language when the language settings change");
});
