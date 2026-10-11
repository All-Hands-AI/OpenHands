import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SetupLlmStep } from "#/components/features/onboarding/steps/setup-llm-step";
import type { SdkSectionSaveControl } from "#/components/features/settings/sdk-settings/sdk-section-page";
import ProfilesService from "#/api/profiles-service/profiles-service.api";
import { renderWithProviders } from "../../../test-utils";

const saveProfile = vi.hoisted(() => vi.fn());
const activateProfile = vi.hoisted(() => vi.fn());
const applyAgentProfile = vi.hoisted(() => vi.fn());
const displayErrorToast = vi.hoisted(() => vi.fn());
const saveControlSave = vi.hoisted(() => vi.fn());
let finishSettingsSave: (() => void) | undefined;
const mockBackendState = vi.hoisted(() => ({
  kind: "local" as "local" | "cloud",
}));
const mockProfilesState = vi.hoisted(() => ({
  active_profile: null as string | null,
  profiles: [] as Array<{ name: string; api_key_set?: boolean }>,
}));

const formState = vi.hoisted(() => ({
  llm: {} as Record<string, unknown>,
  view: "basic" as "basic" | "all",
  initialOverrides: null as Record<string, unknown> | null,
  isDirty: true,
}));

vi.mock("#/contexts/active-backend-context", () => ({
  useActiveBackend: () => ({
    backend: { kind: mockBackendState.kind, id: "test-backend" },
  }),
}));

vi.mock("#/hooks/query/use-llm-profiles", () => ({
  useLlmProfiles: () => ({
    data: mockProfilesState,
    isLoading: false,
  }),
}));

vi.mock("#/api/profiles-service/profiles-service.api", () => ({
  default: {
    getProfile: vi.fn(),
  },
}));

vi.mock("#/hooks/mutation/use-save-llm-profile", () => ({
  useSaveLlmProfile: () => ({ mutateAsync: saveProfile }),
}));

vi.mock("#/hooks/mutation/use-activate-llm-profile", () => ({
  useActivateLlmProfile: () => ({ mutateAsync: activateProfile }),
}));

vi.mock("#/hooks/mutation/use-apply-onboarding-agent-profile", () => ({
  useApplyOnboardingAgentProfile: () => applyAgentProfile,
}));

vi.mock("#/hooks/query/use-free-models", () => ({
  useDefaultModel: () => null,
  useDefaultModelReady: () => true,
}));

vi.mock("#/utils/custom-toast-handlers", () => ({
  displayErrorToast,
}));

vi.mock("#/routes/llm-settings", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  const React = await import("react");
  return {
    ...actual,
    LlmSettingsScreen: ({
      initialValueOverrides,
      onSaveControlChange,
      onSaveSuccess,
    }: {
      initialValueOverrides?: Record<string, unknown>;
      onSaveControlChange: (control: SdkSectionSaveControl) => void;
      onSaveSuccess: () => void;
    }) => {
      formState.initialOverrides = initialValueOverrides ?? null;
      const canonicalLlm = formState.llm;
      finishSettingsSave = onSaveSuccess;
      React.useEffect(() => {
        const buildControl = (isDirty: boolean): SdkSectionSaveControl => ({
          save: () => {
            saveControlSave();
            onSaveControlChange(buildControl(false));
            finishSettingsSave?.();
          },
          isSaving: false,
          isDirty,
          values: Object.fromEntries(
            Object.entries(canonicalLlm).map(([key, value]) => [
              `llm.${key}`,
              String(value),
            ]),
          ),
          view: formState.view,
          getDirtyPayload: () => ({ llm: canonicalLlm }),
          getSavePayload: () => ({
            agent_settings_diff: { llm: canonicalLlm },
          }),
        });
        onSaveControlChange(buildControl(formState.isDirty));
      }, [onSaveControlChange]);
      return <div data-testid="llm-settings-screen" />;
    },
  };
});

describe("SetupLlmStep", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockBackendState.kind = "local";
    mockProfilesState.active_profile = null;
    mockProfilesState.profiles = [];
    formState.llm = {
      model: "gpt-5.6-luna",
      auth_type: "subscription",
      subscription_vendor: "openai",
      temperature: 0.2,
    };
    formState.view = "basic";
    formState.initialOverrides = null;
    formState.isDirty = true;
    finishSettingsSave = undefined;
    saveProfile.mockResolvedValue(undefined);
    activateProfile.mockResolvedValue(undefined);
    applyAgentProfile.mockResolvedValue(undefined);
  });

  it("persists and activates the profile on local backend without calling saveControl.save()", async () => {
    const onNext = vi.fn();
    renderWithProviders(<SetupLlmStep onBack={vi.fn()} onNext={onNext} />);

    await userEvent.click(await screen.findByTestId("onboarding-llm-next"));

    await waitFor(() => {
      expect(saveProfile).toHaveBeenCalledWith({
        name: "gpt-5.6-luna",
        request: {
          llm: {
            model: "gpt-5.6-luna",
            auth_type: "subscription",
            subscription_vendor: "openai",
            provider_connection_id: null,
            temperature: 0.2,
          },
          include_secrets: true,
        },
      });
    });
    expect(activateProfile).toHaveBeenCalledWith("gpt-5.6-luna");
    expect(applyAgentProfile).toHaveBeenCalledWith({
      agent_kind: "openhands",
      llm_profile_ref: "gpt-5.6-luna",
    });
    expect(saveControlSave).not.toHaveBeenCalled();
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it("preserves typed advanced options and base URL when creating the activated profile in All view", async () => {
    formState.view = "all";
    formState.llm = {
      model: "openai/gpt-4o-mini",
      api_key: "test-key",
      base_url: "http://localhost:19118/v1",
      timeout: 3,
      num_retries: 1,
      retry_min_wait: 0,
      retry_max_wait: 0,
      stream: true,
    };
    const onNext = vi.fn();
    renderWithProviders(<SetupLlmStep onBack={vi.fn()} onNext={onNext} />);

    await userEvent.click(await screen.findByTestId("onboarding-llm-next"));

    await waitFor(() => {
      expect(saveProfile).toHaveBeenCalledWith({
        name: "gpt-4o-mini",
        request: {
          llm: {
            ...formState.llm,
            auth_type: "api_key",
            subscription_vendor: null,
            provider_connection_id: null,
          },
          include_secrets: true,
        },
      });
    });
    expect(activateProfile).toHaveBeenCalledWith("gpt-4o-mini");
    expect(applyAgentProfile).toHaveBeenCalledWith({
      agent_kind: "openhands",
      llm_profile_ref: "gpt-4o-mini",
    });
    expect(saveControlSave).not.toHaveBeenCalled();
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it("re-onboarding with an active profile seeds the form with the active profile details", async () => {
    mockProfilesState.active_profile = "deepseek-custom";
    mockProfilesState.profiles = [
      { name: "deepseek-custom", api_key_set: true },
    ];
    vi.mocked(ProfilesService.getProfile).mockResolvedValueOnce({
      name: "deepseek-custom",
      api_key_set: true,
      config: {
        model: "openai/deepseek-chat",
        base_url: "https://api.deepseek.com/v1",
        api_key: "enc:existing-secret",
      },
    });

    renderWithProviders(<SetupLlmStep onBack={vi.fn()} onNext={vi.fn()} />);

    await waitFor(() => {
      expect(formState.initialOverrides).not.toBeNull();
      expect(formState.initialOverrides?.["llm.model"]).toBe(
        "openai/deepseek-chat",
      );
      expect(formState.initialOverrides?.["llm.base_url"]).toBe(
        "https://api.deepseek.com/v1",
      );
      expect(formState.initialOverrides?.["llm.api_key"]).toBe(
        "enc:existing-secret",
      );
    });
  });

  it("re-points agent profile to active LLM profile on Next even when form is untouched", async () => {
    formState.isDirty = false;
    mockProfilesState.active_profile = "deepseek-custom";
    mockProfilesState.profiles = [
      { name: "deepseek-custom", api_key_set: true },
    ];
    vi.mocked(ProfilesService.getProfile).mockResolvedValueOnce({
      name: "deepseek-custom",
      api_key_set: true,
      config: {
        model: "openai/deepseek-chat",
      },
    });

    const onNext = vi.fn();
    renderWithProviders(<SetupLlmStep onBack={vi.fn()} onNext={onNext} />);

    await userEvent.click(await screen.findByTestId("onboarding-llm-next"));

    await waitFor(() => {
      expect(applyAgentProfile).toHaveBeenCalledWith({
        agent_kind: "openhands",
        llm_profile_ref: "deepseek-custom",
      });
      expect(onNext).toHaveBeenCalledTimes(1);
    });
  });

  it("calls saveControl.save() when onboarding on cloud backend", async () => {
    mockBackendState.kind = "cloud";
    const onNext = vi.fn();
    renderWithProviders(<SetupLlmStep onBack={vi.fn()} onNext={onNext} />);

    await userEvent.click(await screen.findByTestId("onboarding-llm-next"));

    await waitFor(() => {
      expect(saveControlSave).toHaveBeenCalledTimes(1);
    });
  });

  it.each([
    ["profile save", saveProfile],
    ["profile activation", activateProfile],
  ])("does not advance when %s fails", async (_label, failingMutation) => {
    failingMutation.mockRejectedValueOnce(new Error("profile unavailable"));
    const onNext = vi.fn();
    renderWithProviders(<SetupLlmStep onBack={vi.fn()} onNext={onNext} />);

    await userEvent.click(await screen.findByTestId("onboarding-llm-next"));

    await waitFor(() => expect(displayErrorToast).toHaveBeenCalled());
    expect(onNext).not.toHaveBeenCalled();
    expect(applyAgentProfile).not.toHaveBeenCalled();
    const nextButton = screen.getByTestId("onboarding-llm-next");
    expect(nextButton).toBeEnabled();

    await userEvent.click(nextButton);
    await waitFor(() => expect(onNext).toHaveBeenCalledTimes(1));
  });
});
