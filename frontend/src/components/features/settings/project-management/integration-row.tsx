import React from "react";

import { useIntegrationStatus } from "#/hooks/query/use-integration-status";
import { useLinkIntegration } from "#/hooks/mutation/use-link-integration";
import { useUnlinkIntegration } from "#/hooks/mutation/use-unlink-integration";
import { useValidateIntegration } from "#/hooks/mutation/use-validate-integration";
import { ConfirmationModal } from "#/components/features/settings/project-management/confirmation-modal";
import { InfoModal } from "#/components/features/settings/project-management/info-modal";
import { IntegrationButton } from "#/components/features/settings/project-management/integration-button";

interface IntegrationRowProps {
  platform: "jira" | "jira-dc" | "linear";
  platformName: string;
  "data-testid"?: string;
}

export function IntegrationRow({
  platform,
  platformName,
  "data-testid": dataTestId,
}: IntegrationRowProps) {
  const [isConfirmationModalOpen, setConfirmationModalOpen] =
    React.useState(false);
  const [isInfoModalOpen, setInfoModalOpen] = React.useState(false);
  const [isUnlinking, setUnlinking] = React.useState(false);

  const { data: status, isLoading: isStatusLoading } =
    useIntegrationStatus(platform);

  const validateMutation = useValidateIntegration(platform, {
    onSuccess: (data) => {
      if (data.data.status === "active") {
        setUnlinking(false);
        setConfirmationModalOpen(true);
      } else {
        setInfoModalOpen(true);
      }
    },
    onError: () => {
      setInfoModalOpen(true);
    },
  });

  const linkMutation = useLinkIntegration(platform, {
    onSettled: () => {
      setConfirmationModalOpen(false);
    },
  });

  const unlinkMutation = useUnlinkIntegration(platform, {
    onSettled: () => {
      setConfirmationModalOpen(false);
    },
  });

  const handleLink = () => {
    validateMutation.mutate();
  };

  const handleUnlink = () => {
    setUnlinking(true);
    setConfirmationModalOpen(true);
  };

  const handleConfirm = () => {
    if (isUnlinking) {
      unlinkMutation.mutate();
    } else {
      linkMutation.mutate();
    }
  };

  const isLinked = status === "active";
  const isLoading =
    isStatusLoading ||
    validateMutation.isPending ||
    linkMutation.isPending ||
    unlinkMutation.isPending;

  return (
    <div className="flex items-center justify-between" data-testid={dataTestId}>
      <span className="font-medium">{platformName}</span>
      <IntegrationButton
        isLoading={isLoading}
        isLinked={isLinked}
        onClick={isLinked ? handleUnlink : handleLink}
        data-testid={`${platform}-integration-button`}
      />
      <ConfirmationModal
        isOpen={isConfirmationModalOpen}
        onClose={() => setConfirmationModalOpen(false)}
        onConfirm={handleConfirm}
        platformName={platformName}
        isUnlinking={isUnlinking}
      />
      <InfoModal
        isOpen={isInfoModalOpen}
        onClose={() => setInfoModalOpen(false)}
        platformName={platformName}
      />
    </div>
  );
}
