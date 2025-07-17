import React from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

import { I18nKey } from "#/i18n/declaration";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { ConfirmationModal } from "#/components/features/settings/project-management/confirmation-modal";
import { InfoModal } from "#/components/features/settings/project-management/info-modal";
import { IntegrationButton } from "#/components/features/settings/project-management/integration-button";
import { openHands } from "#/api/open-hands-axios";

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
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  const [isConfirmationModalOpen, setConfirmationModalOpen] =
    React.useState(false);
  const [isInfoModalOpen, setInfoModalOpen] = React.useState(false);
  const [isUnlinking, setUnlinking] = React.useState(false);

  const { data: status, isLoading: isStatusLoading } = useQuery({
    queryKey: ["integration-status", platform],
    queryFn: async () => {
      try {
        const response = await openHands.get(
          `/integration/${platform}/users/me`,
        );
        return response.data.status;
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return "inactive";
        }
        throw error;
      }
    },
  });

  const validateMutation = useMutation({
    mutationFn: () => openHands.get(`/integration/${platform}/validate`),
    onSuccess: (data) => {
      if (data.data.status === "active") {
        setUnlinking(false);
        setConfirmationModalOpen(true);
      } else {
        setInfoModalOpen(true);
      }
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        setInfoModalOpen(true);
      } else {
        const errorMessage = retrieveAxiosErrorMessage(error);
        displayErrorToast(
          errorMessage ||
            t(I18nKey.PROJECT_MANAGEMENT$VALIDATE_INTEGRATION_ERROR),
        );
      }
    },
  });

  const linkMutation = useMutation({
    mutationFn: () => openHands.post(`/integration/${platform}/users`),
    onSuccess: () => {
      displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
      queryClient.invalidateQueries({
        queryKey: ["integration-status", platform],
      });
    },
    onError: (error) => {
      const errorMessage = retrieveAxiosErrorMessage(error);
      displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
    },
    onSettled: () => {
      setConfirmationModalOpen(false);
    },
  });

  const unlinkMutation = useMutation({
    mutationFn: () => openHands.post(`/integration/${platform}/unlink`),
    onSuccess: () => {
      displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
      queryClient.invalidateQueries({
        queryKey: ["integration-status", platform],
      });
    },
    onError: (error) => {
      const errorMessage = retrieveAxiosErrorMessage(error);
      displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
    },
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
