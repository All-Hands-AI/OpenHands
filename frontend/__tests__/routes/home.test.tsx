import { createRemixStub } from "@remix-run/testing";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "#/routes/_index/route";

const renderRemixStub = (config?: { authenticated: boolean }) =>
  createRemixStub([
    {
      path: "/",
      Component: Home,
      loader: () => ({
        ghToken: config?.authenticated ? "ghp_123456" : null,
      }),
    },
  ]);

describe.skip("Home (_index)", () => {
  it("should render", async () => {
    const RemixStub = renderRemixStub();
    render(<RemixStub />);
    await screen.findByText(/let's start building/i);
  });

  it("should load the gh repos if a token is present", async () => {
    const user = userEvent.setup();
    const RemixStub = renderRemixStub({ authenticated: true });
    render(<RemixStub />);

    const repos = await screen.findByPlaceholderText(
      /select a github project/i,
    );
    await user.click(repos);
    // mocked responses from msw
    screen.getByText(/octocat\/hello-world/i);
    screen.getByText(/octocat\/earth/i);
  });

  it("should not load the gh repos if a token is not present", async () => {
    const RemixStub = renderRemixStub();
    render(<RemixStub />);

    const repos = await screen.findByPlaceholderText(
      /select a github project/i,
    );
    await userEvent.click(repos);
    expect(screen.queryByText(/octocat\/hello-world/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/octocat\/earth/i)).not.toBeInTheDocument();
  });
});
