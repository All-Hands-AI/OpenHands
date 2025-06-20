import React from "react";
import { IoShareOutline } from "react-icons/io5";
import { VscPlay } from "react-icons/vsc";
import { HiOutlineMenuAlt2 } from "react-icons/hi";
import { Button } from "#/components/ui/button";

interface NewProjectTopNavProps {
  onShare?: () => void;
  onRun?: () => void;
  onDrawerToggle?: () => void;
}

export function NewProjectTopNav({
  onShare,
  onRun,
  onDrawerToggle,
}: NewProjectTopNavProps) {
  // Demo project name - replace with actual hook when available
  const projectName = "My Project";

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-base">
      <div className="flex items-center">
        <h1 className="text-lg font-semibold text-content">{projectName}</h1>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onShare}
          className="text-content-secondary hover:text-content"
        >
          <IoShareOutline className="w-5 h-5" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onRun}
          className="text-content-secondary hover:text-content"
        >
          <VscPlay className="w-5 h-5" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onDrawerToggle}
          className="text-content-secondary hover:text-content"
        >
          <HiOutlineMenuAlt2 className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
}
