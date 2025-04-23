import React from "react";
import { useTranslation } from "react-i18next";
import { useConversation } from "#/context/conversation-context";
import { I18nKey } from "#/i18n/declaration";

function VSCodeTab() {
  const { t } = useTranslation();
  const { conversationId } = useConversation();
  const [vsCodeUrl, setVsCodeUrl] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function fetchVSCodeUrl() {
      if (!conversationId) return;

      try {
        setIsLoading(true);
        const response = await fetch(
          `/api/conversations/${conversationId}/vscode-url`,
        );
        const data = await response.json();

        if (data.vscode_url) {
          setVsCodeUrl(data.vscode_url);
        } else {
          setError("VS Code URL not available");
        }
      } catch (err) {
        setError("Failed to fetch VS Code URL");
        console.error("Error fetching VS Code URL:", err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchVSCodeUrl();
  }, [conversationId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center w-full h-full p-10">
        <span className="text-neutral-400 font-bold">Loading VS Code...</span>
      </div>
    );
  }

  if (error || !vsCodeUrl) {
    return (
      <div className="flex items-center justify-center w-full h-full p-10">
        <span className="text-neutral-400 font-bold">
          {error || "VS Code URL not available"}
        </span>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <iframe
        title={t(I18nKey.VSCODE$TITLE) || "VS Code"}
        src={vsCodeUrl}
        className="w-full h-full border-0"
        allow="clipboard-read; clipboard-write"
      />
    </div>
  );
}

export default VSCodeTab;
