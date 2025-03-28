import React from "react";

interface ConnectToRepoProps {
  children: React.ReactNode;
}

export function ConnectToRepo({ children }: ConnectToRepoProps) {
  return (
    <div className="w-full">
      <h2 className="text-xl font-semibold mb-4">Connect to a Repo</h2>
      <div className="w-full">{children}</div>
      <div className="mt-4 flex flex-col gap-2">
        <button
          type="button"
          className="w-full bg-[#2A2A2A] text-white py-2 px-4 rounded-md border border-[#525252] hover:bg-[#333333] transition-colors"
        >
          Launch
        </button>
        <div className="flex flex-col gap-2 mt-2">
          <button
            type="button"
            className="text-white hover:underline text-sm text-left"
          >
            Add GitHub repos
          </button>
          <button
            type="button"
            className="text-white hover:underline text-sm text-left"
          >
            Add GitLab repos
          </button>
        </div>
      </div>
    </div>
  );
}
