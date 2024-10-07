import { describe, expect, it } from "vitest";
import { createRemixStub } from "@remix-run/testing";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App, { clientLoader } from "#/root";

const RemixStub = createRemixStub([
  {
    path: "/",
    Component: App,
    loader: clientLoader,
  },
]);

describe.skip("Root", () => {
  it("should render", async () => {
    render(<RemixStub />);
    await screen.findByTestId("link-to-main");
  });

  describe("Auth Modal", () => {
    it("should display the auth modal on first time visit", async () => {
      render(<RemixStub />);
      await screen.findByTestId("auth-modal");
    });

    it("should close the auth modal on accepting the terms", async () => {
      const user = userEvent.setup();
      render(<RemixStub />);
      await screen.findByTestId("auth-modal");
      await user.click(screen.getByTestId("accept-terms"));
      await user.click(screen.getByRole("button", { name: /continue/i }));

      expect(screen.queryByTestId("auth-modal")).not.toBeInTheDocument();
      expect(screen.getByTestId("link-to-main")).toBeInTheDocument();
    });

    it.todo("should not display the auth modal on subsequent visits");
  });
});
