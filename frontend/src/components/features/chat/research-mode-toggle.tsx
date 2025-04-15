import React from "react";
import { useSettings } from "#/hooks/query/use-settings";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useEndSession } from "#/hooks/use-end-session";
import {
  displaySuccessToast,
  displayErrorToast,
} from "#/utils/custom-toast-handlers";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { BrandButton } from "#/components/features/settings/brand-button";

export function ResearchModeToggle() {
  const { data: settings } = useSettings();
  const { mutate: saveSettings } = useSaveSettings();
  const endSession = useEndSession();

  const [isResearchMode, setIsResearchMode] = React.useState(false);
  const [showConfirmModal, setShowConfirmModal] = React.useState(false);

  React.useEffect(() => {
    if (settings) {
      // Check if we're using the read-only agent
      setIsResearchMode(settings.AGENT === "ReadOnlyAgent");
    }
  }, [settings]);

  const toggleResearchMode = () => {
    if (!settings) return;

    // Show confirmation modal before switching modes
    setShowConfirmModal(true);
  };

  const confirmModeSwitch = () => {
    if (!settings) return;

    const newSettings = {
      ...settings,
      // Switch between the two agent types
      AGENT: isResearchMode ? "CodeActAgent" : "ReadOnlyAgent",
    };

    saveSettings(newSettings, {
      onSuccess: () => {
        setIsResearchMode(!isResearchMode);
        endSession();
        displaySuccessToast(
          !isResearchMode
            ? "Switched to Research Mode. Only read-only tools will be available."
            : "Switched to Execute Mode. All tools are now available.",
        );
        setShowConfirmModal(false);
      },
      onError: (error) => {
        displayErrorToast(`Failed to switch modes: ${error.message}`);
        setShowConfirmModal(false);
      },
    });
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleResearchMode}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
            isResearchMode
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "bg-green-600 text-white hover:bg-green-700"
          }`}
          title={
            isResearchMode
              ? "Currently in Research Mode (read-only tools)"
              : "Currently in Execute Mode (all tools)"
          }
        >
          {isResearchMode ? "Research Mode" : "Execute Mode"}
        </button>
      </div>

      {showConfirmModal && (
        <ModalBackdrop>
          <div className="bg-base-secondary p-6 rounded-xl flex flex-col gap-4 border border-tertiary max-w-md">
            <h2 className="text-xl font-semibold">
              Switch to {isResearchMode ? "Execute" : "Research"} Mode?
            </h2>
            <p className="text-sm">
              {isResearchMode
                ? "Switching to Execute Mode will start a new session with full tool access. Your current research session will end."
                : "Switching to Research Mode will start a new session with read-only tools. Your current session will end."}
            </p>
            <p className="text-sm font-medium">
              Tip: Copy any important information from this session before
              switching.
            </p>
            <div className="flex justify-end gap-3 mt-2">
              <BrandButton
                type="button"
                variant="secondary"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancel
              </BrandButton>
              <BrandButton
                type="button"
                variant="primary"
                onClick={confirmModeSwitch}
              >
                Switch Mode
              </BrandButton>
            </div>
          </div>
        </ModalBackdrop>
      )}
    </>
  );
}
