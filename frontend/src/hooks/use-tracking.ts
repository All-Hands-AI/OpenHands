import posthog from "posthog-js";
import { useConfig } from "./query/use-config";
import { useSettings } from "./query/use-settings";
import { Provider } from "#/types/settings";

/**
 * Hook that provides tracking functions with automatic data collection
 * from available hooks (config, settings, etc.)
 */
export const useTracking = () => {
  const { data: config } = useConfig();
  const { data: settings } = useSettings();

  // Common properties included in all tracking events
  const commonProperties = {
    app_surface: config?.APP_MODE || "unknown",
    plan_tier: null,
    current_url: window.location.href,
    user_email: settings?.EMAIL || settings?.GIT_USER_EMAIL || null,
  };

  const trackLoginButtonClick = ({ provider }: { provider: Provider }) => {
    posthog.capture("login_button_clicked", {
      provider,
      ...commonProperties,
    });
  };

  const trackConversationCreated = ({
    hasRepository,
  }: {
    hasRepository: boolean;
  }) => {
    posthog.capture("conversation_created", {
      has_repository: hasRepository,
      ...commonProperties,
    });
  };

  return {
    trackLoginButtonClick,
    trackConversationCreated,
  };
};
