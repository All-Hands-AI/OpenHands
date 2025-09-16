import { ChevronDown, ChevronRight } from "lucide-react";
import { Microagent } from "#/api/open-hands.types";
import { Typography } from "#/ui/typography";
import { MicroagentTriggers } from "./microagent-triggers";
import { MicroagentContent } from "./microagent-content";

interface MicroagentItemProps {
  agent: Microagent;
  isExpanded: boolean;
  onToggle: (agentName: string) => void;
}

export function MicroagentItem({
  agent,
  isExpanded,
  onToggle,
}: MicroagentItemProps) {
  return (
    <div className="rounded-md overflow-hidden">
      <button
        type="button"
        onClick={() => onToggle(agent.name)}
        className="w-full py-3 px-2 text-left flex items-center justify-between hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center">
          <Typography.Text className="font-bold text-gray-100">
            {agent.name}
          </Typography.Text>
        </div>
        <div className="flex items-center">
          <Typography.Text className="px-2 py-1 text-xs rounded-full bg-gray-800 mr-2">
            {agent.type === "repo" ? "Repository" : "Knowledge"}
          </Typography.Text>
          <Typography.Text className="text-gray-300">
            {isExpanded ? (
              <ChevronDown size={18} />
            ) : (
              <ChevronRight size={18} />
            )}
          </Typography.Text>
        </div>
      </button>

      {isExpanded && (
        <div className="px-2 pb-3 pt-1">
          <MicroagentTriggers triggers={agent.triggers} />
          <MicroagentContent content={agent.content} />
        </div>
      )}
    </div>
  );
}
