import { useTranslation } from "react-i18next";
import { RefreshCw } from "lucide-react";
import { BaseModalTitle } from "#/components/shared/modals/confirmation-modals/base-modal";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../settings/brand-button";

interface MicroagentsModalHeaderProps {
  isAgentReady: boolean;
  isLoading: boolean;
  isRefetching: boolean;
  onRefresh: () => void;
}

export function MicroagentsModalHeader({
  isAgentReady,
  isLoading,
  isRefetching,
  onRefresh,
}: MicroagentsModalHeaderProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6 w-full">
      <div className="flex items-center justify-between w-full">
        <BaseModalTitle title={t(I18nKey.MICROAGENTS_MODAL$TITLE)} />
        {isAgentReady && (
          <BrandButton
            testId="refresh-microagents"
            type="button"
            variant="primary"
            className="flex items-center gap-2"
            onClick={onRefresh}
            isDisabled={isLoading || isRefetching}
          >
            <RefreshCw
              size={16}
              className={`${isRefetching ? "animate-spin" : ""}`}
            />
            {t(I18nKey.BUTTON$REFRESH)}
          </BrandButton>
        )}
      </div>
    </div>
  );
}
