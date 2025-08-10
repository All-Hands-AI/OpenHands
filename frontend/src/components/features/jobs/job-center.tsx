/* eslint-disable i18next/no-literal-string */
import React from "react";
import OpenHands from "#/api/open-hands";

interface JobCenterProps {
  conversationId: string;
  initialJobId?: string | null;
}

interface RepoJobStatus {
  id: string;
  type: string;
  status: string;
  progress: number;
  result?: unknown;
  error?: string;
}

export function JobCenter({
  conversationId,
  initialJobId = null,
}: JobCenterProps) {
  const [jobId, setJobId] = React.useState<string | null>(initialJobId);
  const [status, setStatus] = React.useState<RepoJobStatus | null>(null);
  const [inputId, setInputId] = React.useState("");

  React.useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    const poll = async () => {
      if (!jobId) return;
      try {
        const data = await OpenHands.getRepoJobStatus(conversationId, jobId);
        setStatus(data);
        if (data.status === "COMPLETED" || data.status === "FAILED") return;
      } catch (e) {
        return;
      }
      timer = setTimeout(poll, 1000);
    };
    poll();
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [conversationId, jobId]);

  return (
    <div className="border border-tertiary rounded p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <input
          className="bg-tertiary border border-tertiary-alt rounded px-2 py-1"
          placeholder="Job ID"
          value={inputId}
          onChange={(e) => setInputId(e.target.value)}
        />
        <button
          className="px-2 py-1 border rounded"
          type="button"
          onClick={() => setJobId(inputId)}
        >
          Track
        </button>
      </div>
      {status && (
        <div className="text-sm">
          <div>ID: {status.id}</div>
          <div>Status: {status.status}</div>
          <div>Progress: {Math.round((status.progress || 0) * 100)}%</div>
          {status.error && (
            <div className="text-red-400">Error: {status.error}</div>
          )}
          {Boolean(status.result) && (
            <div className="truncate">
              Result: {JSON.stringify(status.result)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
