import { Icon, Typography } from "@openhands/ui";
import CodeBranchIcon from "#/icons/u-code-branch.svg?react";
import { RecentProject } from "#/api/open-hands.types";

interface RecentProjectCardProps {
  project: RecentProject;
}

export function RecentProjectCard({ project }: RecentProjectCardProps) {
  return (
    <div className="flex flex-col gap-1 py-[14px]">
      <Typography.Text className="text-xs text-white leading-6 font-normal">
        {project.projectName}
      </Typography.Text>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon icon="Github" />
          <Typography.Text className="text-xs text-[#A3A3A3] leading-6 font-normal">
            {project.repositoryName}
          </Typography.Text>
        </div>
        <div className="flex items-center gap-1">
          <CodeBranchIcon width={12} height={12} color="#A3A3A3" />
          <Typography.Text className="text-xs text-[#A3A3A3] leading-4 font-normal max-w-[124px] truncate">
            {project.pr}
          </Typography.Text>
        </div>
        <Typography.Text className="text-xs text-[#A3A3A3] leading-4 font-normal">
          {project.createdAt}
        </Typography.Text>
      </div>
    </div>
  );
}
