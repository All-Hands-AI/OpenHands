import { useQuery } from "@tanstack/react-query";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { useSettings } from "#/hooks/query/use-settings";
import { ModalBackdrop } from "../modal-backdrop";
import { AccountSettingsForm } from "./account-settings-form";
import { useConfig } from "#/hooks/query/use-config";

interface AccountSettingsModalProps {
  onClose: () => void;
}

export function AccountSettingsModal({ onClose }: AccountSettingsModalProps) {
  const user = useGitHubUser();
  const { data: config } = useConfig();
  const { data: settings } = useSettings();
  const { data } = useQuery({
    queryKey: [user.data?.login, "balance"],
    queryFn: async () => ({ balance: 12.34 }),
    enabled: config?.APP_MODE === "saas",
  });

  // FIXME: Bad practice to use localStorage directly
  const analyticsConsent = localStorage.getItem("analytics-consent");

  return (
    <ModalBackdrop onClose={onClose}>
      {data && <span data-testid="current-balance">${data.balance}</span>}
      <AccountSettingsForm
        onClose={onClose}
        selectedLanguage={settings.LANGUAGE}
        gitHubError={user.isError}
        analyticsConsent={analyticsConsent}
      />
    </ModalBackdrop>
  );
}
