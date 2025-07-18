import { MicroagentManagementMicroagentCard } from "./microagent-management-microagent-card";
import { MicroagentManagementAddMicroagentButton } from "./microagent-management-add-microagent-button";

export function MicroagentManagementMicroagents() {
  const microagents = [
    {
      id: "no-comments",
      name: "No comments",
      repositoryUrl: "fairwinds/polaris/Repo Overview",
      createdAt: "05/30/2025",
    },
    {
      id: "tell-me-a-joke",
      name: "Tell me a joke",
      repositoryUrl: ".openhands/microagents/Repo Overview",
      createdAt: "05/30/2025",
    },
  ];

  const numberOfMicroagents = microagents.length;

  if (numberOfMicroagents === 0) {
    return null;
  }

  return (
    <div>
      <div className="flex items-center justify-end pb-4">
        <MicroagentManagementAddMicroagentButton />
      </div>
      {microagents.map((microagent) => (
        <div key={microagent.id} className="pb-4">
          <MicroagentManagementMicroagentCard microagent={microagent} />
        </div>
      ))}
    </div>
  );
}
