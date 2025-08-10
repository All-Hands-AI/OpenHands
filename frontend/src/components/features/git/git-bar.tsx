/* eslint-disable i18next/no-literal-string */
import React from "react";
import OpenHands from "#/api/open-hands";
import { BrandButton } from "#/components/features/settings/brand-button";

interface GitBarProps {
  conversationId: string;
}

export function GitBar({ conversationId }: GitBarProps) {
  const [branchName, setBranchName] = React.useState("");
  const [commitMsg, setCommitMsg] = React.useState("");
  const [prTitle, setPrTitle] = React.useState("");
  const [prUrl, setPrUrl] = React.useState<string | null>(null);
  const [isBusy, setIsBusy] = React.useState(false);

  const createBranch = async () => {
    if (!branchName.trim()) return;
    setIsBusy(true);
    try {
      await OpenHands.createBranch(conversationId, branchName);
      setBranchName("");
    } finally {
      setIsBusy(false);
    }
  };

  const commit = async () => {
    if (!commitMsg.trim()) return;
    setIsBusy(true);
    try {
      await OpenHands.commitChanges(conversationId, commitMsg);
      setCommitMsg("");
    } finally {
      setIsBusy(false);
    }
  };

  const createPR = async () => {
    if (!prTitle.trim()) return;
    setIsBusy(true);
    try {
      const url = await OpenHands.createPullRequest(conversationId, prTitle);
      setPrUrl(url);
      setPrTitle("");
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <div className="flex items-center gap-3 border border-tertiary rounded p-3">
      <div className="flex items-center gap-2">
        <input
          className="bg-tertiary border border-tertiary-alt rounded px-2 py-1"
          placeholder="New branch name"
          value={branchName}
          onChange={(e) => setBranchName(e.target.value)}
        />
        <BrandButton
          variant="secondary"
          type="button"
          isDisabled={isBusy || !branchName}
          onClick={createBranch}
        >
          Create Branch
        </BrandButton>
      </div>
      <div className="flex items-center gap-2">
        <input
          className="bg-tertiary border border-tertiary-alt rounded px-2 py-1 w-64"
          placeholder="Commit message"
          value={commitMsg}
          onChange={(e) => setCommitMsg(e.target.value)}
        />
        <BrandButton
          variant="secondary"
          type="button"
          isDisabled={isBusy || !commitMsg}
          onClick={commit}
        >
          Commit
        </BrandButton>
      </div>
      <div className="flex items-center gap-2">
        <input
          className="bg-tertiary border border-tertiary-alt rounded px-2 py-1 w-64"
          placeholder="PR title"
          value={prTitle}
          onChange={(e) => setPrTitle(e.target.value)}
        />
        <BrandButton
          variant="primary"
          type="button"
          isDisabled={isBusy || !prTitle}
          onClick={createPR}
        >
          Create PR
        </BrandButton>
      </div>
      {prUrl && (
        <a
          className="text-blue-400 hover:underline"
          href={prUrl}
          target="_blank"
          rel="noreferrer"
        >
          View PR
        </a>
      )}
    </div>
  );
}
