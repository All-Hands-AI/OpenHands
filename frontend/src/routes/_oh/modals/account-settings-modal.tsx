import { AccountSettingsForm } from "#/components/modals/account-settings-form";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";
import { useUserPrefs } from "#/context/user-prefs-context";
import { useGitHubUser } from "#/hooks/query/use-github-user";

interface AccountSettingsModalProps {
  onClose: () => void;
}

export function AccountSettingsModal({ onClose }: AccountSettingsModalProps) {
  const user = useGitHubUser();
  const { settings } = useUserPrefs();

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
