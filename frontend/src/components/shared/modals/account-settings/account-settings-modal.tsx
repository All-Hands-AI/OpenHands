import { useGitHubUser } from "#/hooks/query/use-github-user";
import { useSettings } from "#/hooks/query/use-settings";
import { ModalBackdrop } from "../modal-backdrop";
import { AccountSettingsForm } from "./account-settings-form";

interface AccountSettingsModalProps {
  onClose: () => void;
}

export function AccountSettingsModal({ onClose }: AccountSettingsModalProps) {
  const user = useGitHubUser();
  const { data: settings } = useSettings();

  // FIXME: Bad practice to use localStorage directly
  const analyticsConsent = localStorage.getItem("analytics-consent");

  return (
    <ModalBackdrop onClose={onClose}>
      <AccountSettingsForm
        onClose={onClose}
        selectedLanguage={settings.LANGUAGE}
        gitHubError={user.isError}
        analyticsConsent={analyticsConsent}
      />
    </ModalBackdrop>
  );
}
