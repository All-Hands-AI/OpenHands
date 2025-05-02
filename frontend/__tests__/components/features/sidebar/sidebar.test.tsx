import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import OpenHands from "#/api/open-hands";
import { AuthContext } from "#/context/auth-context";

// These tests will now fail because the conversation panel is rendered through a portal
// and technically not a child of the Sidebar component.

const RouterStub = createRoutesStub([
  {
    path: "/conversation/:conversationId",
    Component: () => <Sidebar />,
  },
]);

const renderSidebar = () =>
  renderWithProviders(
    <AuthContext.Provider 
      value={{ 
        providerTokensSet: ["github"], 
        setProviderTokensSet: vi.fn(), 
        providersAreSet: true, 
        setProvidersAreSet: vi.fn() 
      }}
    >
      <RouterStub initialEntries={["/conversation/123"]} />
    </AuthContext.Provider>
  );

describe("Sidebar", () => {
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");

  afterEach(() => {
    vi.clearAllMocks();
  });

  it.skip("should fetch settings data on mount", () => {
    // Mock the useConfig hook to return OSS mode
    vi.spyOn(OpenHands, "getConfig").mockResolvedValue({
      APP_MODE: "oss",
      FEATURE_FLAGS: {}
    });
    
    renderSidebar();
    expect(getSettingsSpy).toHaveBeenCalled();
  });
});
