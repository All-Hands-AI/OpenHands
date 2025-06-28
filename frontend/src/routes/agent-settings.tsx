import React from "react";
import { useTranslation } from "react-i18next";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useSettings } from "#/hooks/query/use-settings";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";

export function AgentSettings() {
  const { t } = useTranslation();
  const { data: settings } = useSettings();
  const { mutateAsync: saveSettings } = useSaveSettings();

  const [dirtyInputs, setDirtyInputs] = React.useState<Record<string, boolean>>(
    {},
  );

  const isDirty = Object.values(dirtyInputs).some(Boolean);

  const handleSave = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);

    const enableBrowsing = formData.get("enable-browsing") === "on";
    const enableLlmEditor = formData.get("enable-llm-editor") === "on";
    const enableEditor = formData.get("enable-editor") === "on";
    const enableCmd = formData.get("enable-cmd") === "on";
    const enableThink = formData.get("enable-think") === "on";
    const enableFinish = formData.get("enable-finish") === "on";
    const enablePromptExtensions =
      formData.get("enable-prompt-extensions") === "on";
    const enableHistoryTruncation =
      formData.get("enable-history-truncation") === "on";

    const disabledMicroagentsValue = formData.get(
      "disabled-microagents",
    ) as string;
    const disabledMicroagents = disabledMicroagentsValue
      ? disabledMicroagentsValue
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
      : [];

    await saveSettings({
      ENABLE_BROWSING: enableBrowsing,
      ENABLE_LLM_EDITOR: enableLlmEditor,
      ENABLE_EDITOR: enableEditor,
      ENABLE_CMD: enableCmd,
      ENABLE_THINK: enableThink,
      ENABLE_FINISH: enableFinish,
      ENABLE_PROMPT_EXTENSIONS: enablePromptExtensions,
      DISABLED_MICROAGENTS: disabledMicroagents,
      ENABLE_HISTORY_TRUNCATION: enableHistoryTruncation,
    });

    setDirtyInputs({});
  };

  if (!settings) {
    return <div>{t(I18nKey.HOME$LOADING)}</div>;
  }

  return (
    <div className="bg-root-primary flex flex-col h-full overflow-y-auto">
      <div className="flex items-center gap-2 border-b border-border px-4 py-2">
        <span className="font-semibold">
          {t(I18nKey.SETTINGS$AGENT_CONFIGURATION)}
        </span>
      </div>

      <form className="flex flex-col gap-6 px-4 py-6" onSubmit={handleSave}>
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">
            {t(I18nKey.SETTINGS$TOOL_CAPABILITIES)}
          </h3>

          <SettingsSwitch
            testId="enable-browsing-switch"
            name="enable-browsing"
            defaultIsToggled={settings.ENABLE_BROWSING}
            onToggle={(checked) => {
              const isBrowsingDirty = checked !== settings.ENABLE_BROWSING;
              setDirtyInputs((prev) => ({
                ...prev,
                enableBrowsing: isBrowsingDirty,
              }));
            }}
          >
            {t(I18nKey.SETTINGS$ENABLE_BROWSING)}
          </SettingsSwitch>
          <div className="text-sm text-neutral-400">
            {t(I18nKey.SETTINGS$ENABLE_BROWSING_HELP)}
          </div>

          <SettingsSwitch
            testId="enable-cmd-switch"
            name="enable-cmd"
            defaultIsToggled={settings.ENABLE_CMD}
            onToggle={(checked: boolean) => {
              const isCmdDirty = checked !== settings.ENABLE_CMD;
              setDirtyInputs((prev) => ({
                ...prev,
                enableCmd: isCmdDirty,
              }));
            }}
          >
            {t(I18nKey.SETTINGS$ENABLE_CMD)}
          </SettingsSwitch>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold">
            {t(I18nKey.SETTINGS$EDITOR_SETTINGS)}
          </h3>

          <SettingsSwitch
            testId="enable-llm-editor-switch"
            name="enable-llm-editor"
            defaultIsToggled={settings.ENABLE_LLM_EDITOR}
            onToggle={(checked: boolean) => {
              const isLlmEditorDirty = checked !== settings.ENABLE_LLM_EDITOR;
              setDirtyInputs((prev) => ({
                ...prev,
                enableLlmEditor: isLlmEditorDirty,
              }));
            }}
          >
            {t(I18nKey.SETTINGS$ENABLE_LLM_EDITOR)}
          </SettingsSwitch>
          <div className="text-sm text-neutral-400">
            {t(I18nKey.SETTINGS$ENABLE_LLM_EDITOR_HELP)}
          </div>

          <SettingsSwitch
            testId="enable-editor-switch"
            name="enable-editor"
            defaultIsToggled={settings.ENABLE_EDITOR}
            onToggle={(checked: boolean) => {
              const isEditorDirty = checked !== settings.ENABLE_EDITOR;
              setDirtyInputs((prev) => ({
                ...prev,
                enableEditor: isEditorDirty,
              }));
            }}
          >
            {t(I18nKey.SETTINGS$ENABLE_EDITOR)}
          </SettingsSwitch>
          <div className="text-sm text-neutral-400">
            {t(I18nKey.SETTINGS$ENABLE_EDITOR_HELP)}
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold">
            {t(I18nKey.SETTINGS$AGENT_BEHAVIOR)}
          </h3>

          <SettingsSwitch
            testId="enable-think-switch"
            name="enable-think"
            defaultIsToggled={settings.ENABLE_THINK}
            onToggle={(checked: boolean) => {
              const isThinkDirty = checked !== settings.ENABLE_THINK;
              setDirtyInputs((prev) => ({
                ...prev,
                enableThink: isThinkDirty,
              }));
            }}
          >
            {t(I18nKey.SETTINGS$ENABLE_THINK)}
          </SettingsSwitch>
          <div className="text-sm text-neutral-400">
            {t(I18nKey.SETTINGS$ENABLE_THINK_HELP)}
          </div>

          <SettingsSwitch
            testId="enable-finish-switch"
            name="enable-finish"
            defaultIsToggled={settings.ENABLE_FINISH}
            onToggle={(checked: boolean) => {
              const isFinishDirty = checked !== settings.ENABLE_FINISH;
              setDirtyInputs((prev) => ({
                ...prev,
                enableFinish: isFinishDirty,
              }));
            }}
          >
            {t(I18nKey.SETTINGS$ENABLE_FINISH)}
          </SettingsSwitch>
          <div className="text-sm text-neutral-400">
            {t(I18nKey.SETTINGS$ENABLE_FINISH_HELP)}
          </div>

          <SettingsSwitch
            testId="enable-prompt-extensions-switch"
            name="enable-prompt-extensions"
            defaultIsToggled={settings.ENABLE_PROMPT_EXTENSIONS}
            onToggle={(checked: boolean) => {
              const isPromptExtensionsDirty =
                checked !== settings.ENABLE_PROMPT_EXTENSIONS;
              setDirtyInputs((prev) => ({
                ...prev,
                enablePromptExtensions: isPromptExtensionsDirty,
              }));
            }}
          >
            {t(I18nKey.SETTINGS$ENABLE_PROMPT_EXTENSIONS)}
          </SettingsSwitch>
          <div className="text-sm text-neutral-400">
            {t(I18nKey.SETTINGS$ENABLE_PROMPT_EXTENSIONS_HELP)}
          </div>

          <SettingsSwitch
            testId="enable-history-truncation-switch"
            name="enable-history-truncation"
            defaultIsToggled={settings.ENABLE_HISTORY_TRUNCATION}
            onToggle={(checked: boolean) => {
              const isHistoryTruncationDirty =
                checked !== settings.ENABLE_HISTORY_TRUNCATION;
              setDirtyInputs((prev) => ({
                ...prev,
                enableHistoryTruncation: isHistoryTruncationDirty,
              }));
            }}
          >
            {t(I18nKey.SETTINGS$ENABLE_HISTORY_TRUNCATION)}
          </SettingsSwitch>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold">
            {t(I18nKey.SETTINGS$MICROAGENT_MANAGEMENT)}
          </h3>

          <SettingsInput
            testId="disabled-microagents-input"
            name="disabled-microagents"
            label={t(I18nKey.SETTINGS$DISABLED_MICROAGENTS)}
            type="text"
            className="w-full max-w-[680px]"
            defaultValue={settings.DISABLED_MICROAGENTS.join(", ")}
            placeholder={t(I18nKey.SETTINGS$DISABLED_MICROAGENTS_PLACEHOLDER)}
            onChange={(value: string) => {
              const currentArray = value
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean);
              const originalArray = settings.DISABLED_MICROAGENTS;

              const isMicroagentsDirty =
                currentArray.length !== originalArray.length ||
                currentArray.some(
                  (item, index) => item !== originalArray[index],
                );

              setDirtyInputs((prev) => ({
                ...prev,
                disabledMicroagents: isMicroagentsDirty,
              }));
            }}
          />
          <div className="text-sm text-neutral-400">
            {t(I18nKey.SETTINGS$DISABLED_MICROAGENTS_HELP)}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={!isDirty}
            className="bg-primary hover:bg-primary/80 text-white px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t(I18nKey.SETTINGS$SAVE_AGENT_SETTINGS)}
          </button>
        </div>
      </form>
    </div>
  );
}

export default AgentSettings;
