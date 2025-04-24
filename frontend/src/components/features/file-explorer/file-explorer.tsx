import React from "react";
import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { ExplorerTree } from "#/components/features/file-explorer/explorer-tree";
import { RootState } from "#/store";
import { I18nKey } from "#/i18n/declaration";
import { useListFiles } from "#/hooks/query/use-list-files";
import { cn } from "#/utils/utils";
import { FileExplorerHeader } from "./file-explorer-header";

interface FileExplorerProps {
  isOpen: boolean;
  onToggle: () => void;
}

export function FileExplorer({ isOpen, onToggle }: FileExplorerProps) {
  const { t } = useTranslation();

  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const { data: paths, refetch, error } = useListFiles();

  const refreshWorkspace = () => {
    if (!RUNTIME_INACTIVE_STATES.includes(curAgentState)) {
      refetch();
    }
  };

  React.useEffect(() => {
    refreshWorkspace();
  }, [curAgentState]);

  return (
    <div data-testid="file-explorer" className="relative h-full">
      <div
        className={cn(
          "bg-base-secondary h-full border-r-1 border-r-neutral-600 flex flex-col",
          !isOpen ? "w-12" : "w-60",
        )}
      >
        <div className="flex flex-col relative h-full px-3 py-2 overflow-hidden">
          <FileExplorerHeader
            isOpen={isOpen}
            onToggle={onToggle}
            onRefreshWorkspace={refreshWorkspace}
          />
          {!error && (
            <div className="overflow-auto flex-grow min-h-0">
              <div style={{ display: !isOpen ? "none" : "block" }}>
                <ExplorerTree files={paths || []} />
              </div>
            </div>
          )}
          {error && (
            <div className="flex flex-col items-center justify-center h-full">
              <p className="text-neutral-300 text-sm">{error.message}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
