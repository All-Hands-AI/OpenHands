import { useTranslation } from "react-i18next";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { Settings } from "#/services/settings";
import { I18nKey } from "#/i18n/declaration";
import { LoadingSpinner } from "../../loading-spinner";
import { ModalBackdrop } from "../modal-backdrop";
import { SettingsForm } from "./settings-form";

interface SettingsModalProps {
  settings: Settings;
  onClose: () => void;
}

export function SettingsModal({ onClose, settings }: SettingsModalProps) {
  const aiConfigOptions = useAIConfigOptions();
  const { t } = useTranslation();

  return (
    <ModalBackdrop onClose={onClose}>
      <div
        data-testid="ai-config-modal"
        className="bg-root-primary min-w-[384px] max-w-[700px] p-6 rounded-xl flex flex-col gap-2"
      >
        {aiConfigOptions.error && (
          <p className="text-danger text-xs">{aiConfigOptions.error.message}</p>
        )}
        <span className="text-xl leading-6 font-semibold -tracking-[0.01em">
          {t(I18nKey.AI_SETTINGS$TITLE)}
        </span>
        <p className="text-xs text-[#A3A3A3]">
          {t(I18nKey.SETTINGS$DESCRIPTION)}
        </p>
        <p className="text-xs text-danger">{t(I18nKey.SETTINGS$WARNING)}</p>
        {aiConfigOptions.isLoading && (
          <div className="flex justify-center">
            <LoadingSpinner size="small" />
          </div>
        )}
        {aiConfigOptions.data && (
          <SettingsForm
            settings={settings}
            models={aiConfigOptions.data?.models}
            agents={aiConfigOptions.data?.agents}
            securityAnalyzers={aiConfigOptions.data?.securityAnalyzers}
            onClose={onClose}
          />
        )}
      </div>
    </ModalBackdrop>
  );
}
