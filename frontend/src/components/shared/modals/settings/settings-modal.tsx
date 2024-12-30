import { useAIConfigOptions } from "#/hooks/query/use-ai-config-options";
import { Settings } from "#/services/settings";
import { LoadingSpinner } from "../../loading-spinner";
import { ModalBackdrop } from "../modal-backdrop";
import { SettingsForm } from "./settings-form";

interface SettingsModalProps {
  settings: Settings;
  onClose: () => void;
}

export function SettingsModal({ onClose, settings }: SettingsModalProps) {
  const aiConfigOptions = useAIConfigOptions();

  return (
    <ModalBackdrop onClose={onClose}>
      <div
        data-testid="ai-config-modal"
        className="bg-root-primary w-[384px] p-6 rounded-xl flex flex-col gap-2"
      >
        {aiConfigOptions.error && (
          <p className="text-danger text-xs">{aiConfigOptions.error.message}</p>
        )}
        <span className="text-xl leading-6 font-semibold -tracking-[0.01em">
          AI Provider Configuration
        </span>
        <p className="text-xs text-[#A3A3A3]">
          To continue, connect an OpenAI, Anthropic, or other LLM account
        </p>
        <p className="text-xs text-danger">
          Changing settings during an active session will end the session
        </p>
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
