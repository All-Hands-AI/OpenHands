import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { OnboardingDigitalOceanConnect } from "#/components/features/onboarding/steps/onboarding-digitalocean-connect";

const bridgeState = vi.hoisted(() => ({
  required: false,
  missing: false,
}));
const saveHostingSessionKeyMock = vi.hoisted(() => vi.fn());

vi.mock("#/api/mars/mars-web-bridge", () => ({
  getMarsWebBridgeAuthRequired: () => bridgeState.required,
  resolveMarsWebBridgeAuth: () => ({
    required: bridgeState.required,
    missing: bridgeState.missing,
  }),
  saveHostingSessionKey: saveHostingSessionKeyMock,
}));

// The DO panel renders the PAT field through ManagedAgentsSignIn; the hosting
// gate is under test here, so stub the panel with the same observable token
// field to prove it appears only after the hosting key is accepted.
vi.mock(
  "#/components/features/backends/managed-agents/digitalocean-connect-panel",
  () => ({
    DigitalOceanConnectPanel: ({
      onConnected,
    }: {
      onConnected: () => void;
    }) => (
      <div>
        <input data-testid="managed-agents-token" />
        <button
          type="button"
          data-testid="do-panel-connected"
          onClick={onConnected}
        />
      </div>
    ),
  }),
);

function renderConnect(onBack = vi.fn(), onConnected = vi.fn()) {
  return render(
    <OnboardingDigitalOceanConnect onBack={onBack} onConnected={onConnected} />,
  );
}

beforeEach(() => {
  bridgeState.required = false;
  bridgeState.missing = false;
  saveHostingSessionKeyMock.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("OnboardingDigitalOceanConnect hosting-auth gate", () => {
  it("shows the DO token form directly when the bridge needs no hosting key", () => {
    renderConnect();
    expect(screen.getByTestId("managed-agents-token")).toBeInTheDocument();
    expect(
      screen.queryByTestId("onboarding-digitalocean-hosting-key"),
    ).not.toBeInTheDocument();
  });

  it("requests the hosting session key first when the bridge requires one the page lacks", () => {
    bridgeState.required = true;
    bridgeState.missing = true;
    renderConnect();

    // Hosting key prompt is visible; the DO token field is not offered yet.
    expect(
      screen.getByTestId("onboarding-digitalocean-hosting-key"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("managed-agents-token"),
    ).not.toBeInTheDocument();
  });

  it("keeps the DO token hidden and stays recoverable when the typed key is rejected", async () => {
    bridgeState.required = true;
    bridgeState.missing = true;
    saveHostingSessionKeyMock.mockRejectedValue(
      Object.assign(new Error("session key required"), {
        message: "session key required",
      }),
    );
    const user = userEvent.setup();
    renderConnect();

    const keyInput = screen.getByTestId("onboarding-digitalocean-hosting-key");
    await user.type(keyInput, "wrong-key");
    await user.click(
      screen.getByTestId("onboarding-digitalocean-hosting-submit"),
    );

    // Error shown, no DO token yet, still on the same view.
    expect(
      await screen.findByTestId("onboarding-digitalocean-hosting-error"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("managed-agents-token"),
    ).not.toBeInTheDocument();
  });

  it("reveals the DO token form once a valid hosting key is accepted", async () => {
    bridgeState.required = true;
    bridgeState.missing = true;
    saveHostingSessionKeyMock.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderConnect();

    await user.type(
      screen.getByTestId("onboarding-digitalocean-hosting-key"),
      "good-key",
    );
    await user.click(
      screen.getByTestId("onboarding-digitalocean-hosting-submit"),
    );

    expect(saveHostingSessionKeyMock).toHaveBeenCalledWith("good-key");
    expect(
      await screen.findByTestId("managed-agents-token"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("onboarding-digitalocean-hosting-key"),
    ).not.toBeInTheDocument();
  });
});
