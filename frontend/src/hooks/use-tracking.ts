import posthog from "posthog-js";
import { useConfig } from "./query/use-config";
import { useSettings } from "./query/use-settings";
import { Provider } from "#/types/settings";

/**
 * Hook that provides tracking functions with automatic data collection
 * from available hooks (config, settings, etc.)
 * All tracking functions respect user consent settings
 */
export const useTracking = () => {
  const { data: config } = useConfig();
  const { data: settings } = useSettings();

  // Check if user has consented to analytics
  const hasConsented = settings?.USER_CONSENTS_TO_ANALYTICS === true;

  // Common properties included in all tracking events
  const commonProperties = {
    app_surface: config?.APP_MODE || "unknown",
    plan_tier: null,
    current_url: window.location.href,
    user_email: settings?.EMAIL || settings?.GIT_USER_EMAIL || null,
  };

  // Helper to safely capture events only if user has consented
  const safeCapture = (eventName: string, properties?: Record<string, unknown>) => {
    if (hasConsented && !posthog.has_opted_out_capturing()) {
      posthog.capture(eventName, properties);
    }
  };

  const trackLoginButtonClick = ({ provider }: { provider: Provider }) => {
    safeCapture("login_button_clicked", {
      provider,
      ...commonProperties,
    });
  };

  const trackConversationCreated = ({
    hasRepository,
  }: {
    hasRepository: boolean;
  }) => {
    safeCapture("conversation_created", {
      has_repository: hasRepository,
      ...commonProperties,
    });
  };

  const trackPushButtonClick = () => {
    safeCapture("push_button_clicked", {
      ...commonProperties,
    });
  };

  const trackPullButtonClick = () => {
    safeCapture("pull_button_clicked", {
      ...commonProperties,
    });
  };

  const trackCreatePrButtonClick = () => {
    safeCapture("create_pr_button_clicked", {
      ...commonProperties,
    });
  };

  const trackGitProviderConnected = ({
    providers,
  }: {
    providers: string[];
  }) => {
    safeCapture("git_provider_connected", {
      providers,
      ...commonProperties,
    });
  };

  return {
    trackLoginButtonClick,
    trackConversationCreated,
    trackPushButtonClick,
    trackPullButtonClick,
    trackCreatePrButtonClick,
    trackGitProviderConnected,
  };
};
