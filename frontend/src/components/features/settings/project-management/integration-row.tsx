import React from "react";

import { useIntegrationStatus } from "#/hooks/query/use-integration-status";
import { useLinkIntegration } from "#/hooks/mutation/use-link-integration";
import { useUnlinkIntegration } from "#/hooks/mutation/use-unlink-integration";
import { useConfigureIntegration } from "#/hooks/mutation/use-configure-integration";
import { useValidateIntegration } from "#/hooks/query/use-validate-integration";
import { ConfirmationModal } from "#/components/features/settings/project-management/confirmation-modal";
import {
  ConfigureButton,
  ConfigureModal,
} from "#/components/features/settings/project-management/configure-modal";
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
  const [isConfigureModalOpen, setConfigureModalOpen] = React.useState(false);
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

  const configureMutation = useConfigureIntegration(platform, {
    onSettled: () => {
      setConfigureModalOpen(false);
    },
  });

  const handleLink = () => {
    validateMutation.mutate();
  };

  const handleUnlink = () => {
    setUnlinking(true);
    setConfirmationModalOpen(true);
  };

  const handleConfigure = () => {
    setConfigureModalOpen(true);
  };

  const handleConfirm = (workspace?: string) => {
    if (isUnlinking) {
      unlinkMutation.mutate();
    } else {
      linkMutation.mutate(workspace || "");
    }
  };

  const handleConfigureConfirm = (data: {
    workspace: string;
    webhookSecret: string;
    serviceAccountEmail: string;
    serviceAccountApiKey: string;
    isActive: boolean;
  }) => {
    configureMutation.mutate(data);
  };

  const isLinked = status === "active";
  const isLoading =
    isStatusLoading ||
    validateMutation.isPending ||
    linkMutation.isPending ||
    unlinkMutation.isPending ||
    configureMutation.isPending;

  return (
    <div className="flex items-center justify-between" data-testid={dataTestId}>
      <span className="font-medium">{platformName}</span>
      <div className="flex items-center gap-6">
        <IntegrationButton
          isLoading={isLoading}
          isLinked={isLinked}
          onClick={isLinked ? handleUnlink : handleLink}
          data-testid={`${platform}-integration-button`}
        />
        <ConfigureButton
          onClick={handleConfigure}
          isDisabled={isLoading}
          data-testid={`${platform}-configure-button`}
        />
      </div>
      <ConfirmationModal
        isOpen={isConfirmationModalOpen}
        onClose={() => setConfirmationModalOpen(false)}
        onConfirm={handleConfirm}
        platformName={platformName}
        isUnlinking={isUnlinking}
      />
      <ConfigureModal
        isOpen={isConfigureModalOpen}
        onClose={() => setConfigureModalOpen(false)}
        onConfirm={handleConfigureConfirm}
        platformName={platformName}
      />
      <InfoModal
        isOpen={isInfoModalOpen}
        onClose={() => setInfoModalOpen(false)}
        platformName={platformName}
      />
    </div>
  );
}
