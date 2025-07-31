import { useTranslation } from "react-i18next";
import { Spinner } from "@heroui/react";
import { useSelector } from "react-redux";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { code } from "../markdown/code";
import { ul, ol } from "../markdown/list";
import { paragraph } from "../markdown/paragraph";
import { anchor } from "../markdown/anchor";
import { RootState } from "#/store";
import { useRepositoryMicroagentContent } from "#/hooks/query/use-repository-microagent-content";
import { I18nKey } from "#/i18n/declaration";

export function MicroagentManagementViewMicroagentContent() {
  const { t } = useTranslation();
  const { selectedMicroagentItem } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { selectedRepository } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { microagent } = selectedMicroagentItem ?? {};

  // Extract owner and repo from full_name (e.g., "owner/repo")
  const [owner, repo] = selectedRepository?.full_name?.split("/") || [];
  const filePath = microagent?.path || "";

  // Fetch microagent content using the new API
  const {
    data: microagentData,
    isLoading,
    error,
  } = useRepositoryMicroagentContent(owner, repo, filePath, true);

  if (!microagent || !selectedRepository) {
    return null;
  }

  return (
    <div className="w-full h-full p-6 bg-[#ffffff1a] rounded-2xl text-white text-sm">
      {isLoading && (
        <div className="flex items-center justify-center w-full h-full">
          <Spinner size="lg" data-testid="loading-microagent-content-spinner" />
        </div>
      )}
      {error && (
        <div className="flex items-center justify-center w-full h-full">
          {t(I18nKey.MICROAGENT_MANAGEMENT$ERROR_LOADING_MICROAGENT_CONTENT)}
        </div>
      )}
      {microagentData && !isLoading && !error && (
        <Markdown
          components={{
            code,
            ul,
            ol,
            a: anchor,
            p: paragraph,
          }}
          remarkPlugins={[remarkGfm, remarkBreaks]}
        >
          {microagentData.content}
        </Markdown>
      )}
    </div>
  );
}
