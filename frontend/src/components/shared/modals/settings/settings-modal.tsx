import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { I18nKey } from "#/i18n/declaration";
import { LoadingSpinner } from "../../loading-spinner";
import { ModalBackdrop } from "../modal-backdrop";
import { SettingsForm } from "./settings-form";
import { Settings } from "#/types/settings";
import { DEFAULT_SETTINGS } from "#/services/settings";

interface SettingsModalProps {
  settings?: Settings;
  onClose: () => void;
}

export function SettingsModal({ onClose, settings }: SettingsModalProps) {
  const aiConfigOptions = useAIConfigOptions();
  const { t } = useTranslation();

  return (
    <ModalBackdrop>
      <div
        data-testid="ai-config-modal"
        className="bg-base-secondary min-w-[384px] m-4 p-6 rounded-xl flex flex-col gap-2 border border-tertiary"
      >
        {aiConfigOptions.error && (
          <p className="text-danger text-xs">{aiConfigOptions.error.message}</p>
        )}
        <span className="text-xl leading-6 font-semibold -tracking-[0.01em]">
          {t(I18nKey.AI_SETTINGS$TITLE)}
        </span>
        <p className="text-xs text-[#A3A3A3]">
          {t(I18nKey.SETTINGS$DESCRIPTION)}{" "}
          {t(I18nKey.SETTINGS$FOR_OTHER_OPTIONS)}
          <Link
            data-testid="advanced-settings-link"
            to="/settings"
            className="underline underline-offset-2 text-white"
          >
            {t(I18nKey.SETTINGS$SEE_ADVANCED_SETTINGS)}
          </Link>
        </p>

        {aiConfigOptions.isLoading && (
          <div className="flex justify-center">
            <LoadingSpinner size="small" />
          </div>
        )}
        {aiConfigOptions.data && (
          <SettingsForm
            settings={settings || DEFAULT_SETTINGS}
            models={aiConfigOptions.data?.models}
            onClose={onClose}
          />
        )}
      </div>
    </ModalBackdrop>
  );
}
