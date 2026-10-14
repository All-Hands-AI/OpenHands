import { SdkSectionPage } from "#/components/features/settings/sdk-settings/sdk-section-page";
import { useConversationWorkspace } from "#/hooks/query/use-conversation-workspace";

// Only a Docker conversation has a container to size.
const CONTAINER_FIELD_KEYS = new Set([
  "container_memory",
  "container_cpus",
  "container_browser",
]);

function RuntimeSettingsScreen() {
  const { isolated, dockerSelectable } = useConversationWorkspace();
  const runsDocker = isolated || dockerSelectable;

  return (
    <SdkSectionPage
      settingsSources={[
        {
          settingsSource: "conversation_settings",
          sectionKeys: ["runtime"],
          excludeKeys: runsDocker ? undefined : CONTAINER_FIELD_KEYS,
        },
      ]}
      testId="runtime-settings-screen"
    />
  );
}

export default RuntimeSettingsScreen;
