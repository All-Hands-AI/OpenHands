import { Typography } from "@openhands/ui";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { RecentProjectCard } from "./recent-project-card";
import { RecentProject } from "#/api/open-hands.types";

export function RecentProjects() {
  const { t } = useTranslation();

  // TODO: mock the recent projects data.
  const recentProjects: RecentProject[] = [
    {
      projectName: "My Awesome Project",
      gitProvider: "github",
      repositoryName: "openartist/vector",
      pr: "feature/user-authentication",
      createdAt: "2m ago",
    },
    {
      projectName: "My Awesome Project",
      gitProvider: "github",
      repositoryName: "openartist/vector",
      pr: "feature/user-authentication",
      createdAt: "2m ago",
    },
    {
      projectName: "My Awesome Project",
      gitProvider: "github",
      repositoryName: "openartist/vector",
      pr: "feature/user-authentication",
      createdAt: "2m ago",
    },
  ];

  return (
    <section
      data-testid="recent-projects"
      className="w-full flex flex-col pr-[16px] py-[10.5px]"
    >
      <div className="flex items-center gap-2">
        <Typography.Text className="text-sm leading-[16px] text-white font-medium">
          {t(I18nKey.COMMON$RECENT_PROJECTS)}
        </Typography.Text>
      </div>

      <div className="flex flex-col">
        {recentProjects.map((project) => (
          <RecentProjectCard key={project.projectName} project={project} />
        ))}
      </div>
    </section>
  );
}
