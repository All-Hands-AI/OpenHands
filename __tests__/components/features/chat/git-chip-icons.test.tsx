import type { ReactElement } from "react";
import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { GitControlBarBranchButton } from "#/components/features/chat/git-control-bar-branch-button";
import { GitControlBarRepoButton } from "#/components/features/chat/git-control-bar-repo-button";
import { GitExternalLinkIcon } from "#/components/features/chat/git-external-link-icon";
import { WorkspaceModeSelector } from "#/components/features/chat/workspace-mode-selector";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("#/hooks/query/use-settings", () => ({
  useSettings: () => ({ data: { provider_tokens_set: {} } }),
}));

// Chip icons must take the theme's ink (`text-contrast`, the same token as the
// chip labels) through `currentColor`. A fixed `color` attribute on the SVG
// overrides that inheritance and made the icons white-on-white in light themes
// (#18657).
describe("git control bar chip icons", () => {
  it.each<[string, () => ReactElement]>([
    [
      "linked branch chip",
      () => (
        <GitControlBarBranchButton
          selectedBranch="main"
          selectedRepository="owner/repo"
          gitProvider="github"
        />
      ),
    ],
    [
      "unlinked branch chip",
      () => (
        <GitControlBarBranchButton
          selectedBranch="main"
          selectedRepository={null}
          gitProvider={null}
        />
      ),
    ],
    [
      "local workspace chip",
      () => (
        <GitControlBarRepoButton
          selectedRepository={null}
          gitProvider={null}
          workspaceName="qa-repo"
        />
      ),
    ],
    ["external link hover", () => <GitExternalLinkIcon />],
    [
      "workspace mode chip",
      () => (
        <WorkspaceModeSelector
          value="local_repo"
          backendKind="local"
          onChange={() => {}}
        />
      ),
    ],
  ])("%s icons inherit the theme ink colour", (_name, renderChip) => {
    const { container } = render(renderChip());

    const icons = Array.from(container.querySelectorAll("svg"));
    expect(icons.length).toBeGreaterThan(0);
    for (const icon of icons) {
      expect(icon).not.toHaveAttribute("color");
      expect(icon.closest(".text-contrast")).not.toBeNull();
    }
  });
});
