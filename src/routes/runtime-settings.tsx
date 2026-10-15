import { SdkSectionPage } from "#/components/features/settings/sdk-settings/sdk-section-page";
import { WorktreeCleanup } from "#/components/features/settings/runtime/worktree-cleanup";

function RuntimeSettingsScreen() {
  return (
    <div className="flex flex-col gap-8">
      <SdkSectionPage
        settingsSources={[
          { settingsSource: "conversation_settings", sectionKeys: ["runtime"] },
        ]}
        testId="runtime-settings-screen"
      />
      <WorktreeCleanup />
    </div>
  );
}

export default RuntimeSettingsScreen;
