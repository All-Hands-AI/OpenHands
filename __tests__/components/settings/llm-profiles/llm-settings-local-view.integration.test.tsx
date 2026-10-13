import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { LlmSettingsLocalView } from "#/components/features/settings/llm-profiles/llm-settings-local-view";
import SettingsService from "#/api/settings-service/settings-service.api";
import ProfilesService from "#/api/profiles-service/profiles-service.api";
import ProviderConnectionsService from "#/api/provider-connections-service/provider-connections-service.api";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import { useFreeModelsStore } from "#/stores/free-models-store";

describe("LLM profile creation with the real embedded form", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    useFreeModelsStore
      .getState()
      .setFlags({ freeModels: new Set(), defaultModel: "openai/gpt-4o" });
    vi.spyOn(ProfilesService, "listProfiles").mockResolvedValue({
      profiles: [],
      active_profile: null,
    });
    vi.spyOn(ProfilesService, "validateProfile").mockResolvedValue({
      valid: true,
    });
    vi.spyOn(ProviderConnectionsService, "list").mockResolvedValue([]);
    vi.spyOn(SettingsService, "getSettings").mockResolvedValue({
      ...MOCK_DEFAULT_USER_SETTINGS,
      agent_settings: {
        ...MOCK_DEFAULT_USER_SETTINGS.agent_settings,
        llm: {
          model: "anthropic/claude-sonnet",
          api_key: "another-profile-key",
          base_url: "https://another-profile.example/v1",
          temperature: 0.4,
        },
      },
    });
  });

  it("saves an untouched displayed option without inheriting another profile's credentials", async () => {
    // Arrange: existing agent settings have a non-default option and credentials.
    const save = vi
      .spyOn(ProfilesService, "saveProfile")
      .mockResolvedValue({ success: true });
    const user = userEvent.setup();
    renderWithProviders(<LlmSettingsLocalView />);

    // Act: create a profile, keeping its displayed temperature unchanged.
    await user.click(await screen.findByTestId("add-llm-profile"));
    await user.click(await screen.findByTestId("sdk-section-all-toggle"));
    expect(screen.getByTestId("sdk-settings-llm.temperature")).toHaveValue(0.4);
    expect(screen.getByTestId("llm-api-key-input")).toHaveValue("");
    expect(screen.getByTestId("base-url-input")).toHaveValue("");
    await user.clear(screen.getByTestId("profile-name-input"));
    await user.type(screen.getByTestId("profile-name-input"), "QA_Inherited");
    await user.type(screen.getByTestId("llm-api-key-input"), "new-profile-key");
    await user.click(screen.getByTestId("save-profile-btn"));

    // Assert: the real schema form's coerced option reaches profile persistence.
    await waitFor(() =>
      expect(save).toHaveBeenCalledWith("QA_Inherited", {
        llm: expect.objectContaining({
          model: "openai/gpt-4o",
          api_key: "new-profile-key",
          temperature: 0.4,
        }),
        include_secrets: true,
      }),
    );
    expect(save.mock.calls[0][1].llm.base_url).not.toBe(
      "https://another-profile.example/v1",
    );
  });
});
