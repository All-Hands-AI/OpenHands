/* eslint-disable i18next/no-literal-string */
import React from "react";
import { useParams } from "react-router";
import OpenHands from "#/api/open-hands";
import { FileTree } from "#/components/features/files/file-tree";
import { EditorPanel } from "#/components/features/files/editor-panel";
import { BrandButton } from "#/components/features/settings/brand-button";
import { GitBar } from "#/components/features/git/git-bar";
import { JobCenter } from "#/components/features/jobs/job-center";

export default function RepoWorkspaceScreen() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const [repoInput, setRepoInput] = React.useState("");
  const [branchInput, setBranchInput] = React.useState("");
  const [currentFile, setCurrentFile] = React.useState<string | null>(null);
  const [isOpening, setIsOpening] = React.useState(false);
  const [cloneJobId, setCloneJobId] = React.useState<string | null>(null);

  if (!conversationId) return null;

  const openRepo = async () => {
    setIsOpening(true);
    try {
      const resp = await OpenHands.openRepo(
        conversationId,
        repoInput || undefined,
        branchInput || undefined,
      );
      if ((resp as unknown as { job_id?: string }).job_id) {
        setCloneJobId((resp as unknown as { job_id: string }).job_id);
      }
    } finally {
      setIsOpening(false);
    }
  };

  return (
    <div className="flex flex-col h-full p-6 gap-4">
      <div className="flex items-end gap-3">
        <div className="flex flex-col">
          <label className="text-xs opacity-70" htmlFor="repo-input">
            Repository (owner/repo)
          </label>
          <input
            id="repo-input"
            className="bg-tertiary border border-tertiary-alt rounded px-2 py-1"
            placeholder="owner/repo"
            value={repoInput}
            onChange={(e) => setRepoInput(e.target.value)}
          />
        </div>
        <div className="flex flex-col">
          <label className="text-xs opacity-70" htmlFor="branch-input">
            Branch
          </label>
          <input
            id="branch-input"
            className="bg-tertiary border border-tertiary-alt rounded px-2 py-1"
            placeholder="(optional)"
            value={branchInput}
            onChange={(e) => setBranchInput(e.target.value)}
          />
        </div>
        <BrandButton
          variant="primary"
          type="button"
          isDisabled={isOpening || !repoInput}
          onClick={openRepo}
        >
          {isOpening ? "Opening..." : "Open"}
        </BrandButton>
      </div>

      <GitBar conversationId={conversationId} />

      <JobCenter conversationId={conversationId} initialJobId={cloneJobId} />

      <div className="grid grid-cols-3 gap-4 h-[70vh]">
        <div className="col-span-1 border border-tertiary rounded">
          <FileTree
            conversationId={conversationId}
            onOpenFile={(p) => setCurrentFile(p)}
          />
        </div>
        <div className="col-span-2 border border-tertiary rounded">
          <EditorPanel conversationId={conversationId} path={currentFile} />
        </div>
      </div>
    </div>
  );
}
