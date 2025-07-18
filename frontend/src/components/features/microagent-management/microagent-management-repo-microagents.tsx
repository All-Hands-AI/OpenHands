import { MicroagentManagementRepoMicroagent } from "./microagent-management-repo-microagent";

export function MicroagentManagementRepoMicroagents() {
  const repoMicroagents = [
    {
      id: "rbren/rss-parser",
      repositoryName: "rbren/rss-parser",
      repositoryUrl: "https://github.com/rbren/rss-parser",
      microagents: [],
    },
    {
      id: "fairwinds/polaris",
      repositoryName: "fairwinds/polaris",
      repositoryUrl: "https://github.com/fairwinds/polaris",
      microagents: [
        {
          id: "no-comments",
          name: "No comments",
          repositoryUrl: "fairwinds/polaris/Repo Overview",
          createdAt: "05/30/2025",
        },
      ],
    },
  ];

  const numberOfRepoMicroagents = repoMicroagents.length;

  if (numberOfRepoMicroagents === 0) {
    return null;
  }

  return (
    <div>
      {repoMicroagents.map((repoMicroagent) => (
        <MicroagentManagementRepoMicroagent
          key={repoMicroagent.id}
          repoMicroagent={repoMicroagent}
        />
      ))}
    </div>
  );
}
