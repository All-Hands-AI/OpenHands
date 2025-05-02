import React, { useEffect, useState } from "react";
import { cn } from "#/utils/utils";

export interface MicroagentInfo {
  name: string;
  trigger: string;
  description: string;
}

interface MicroagentSuggestionsProps {
  query: string;
  isVisible: boolean;
  onSelect: (trigger: string) => void;
  className?: string;
}

export function MicroagentSuggestions({
  query,
  isVisible,
  onSelect,
  className,
}: MicroagentSuggestionsProps) {
  const [microagents, setMicroagents] = useState<MicroagentInfo[]>([]);
  const [filteredMicroagents, setFilteredMicroagents] = useState<
    MicroagentInfo[]
  >([]);
  const [loading, setLoading] = useState(false);

  // Fetch microagents when the component mounts
  useEffect(() => {
    const fetchMicroagents = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/options/microagents");
        if (response.ok) {
          const data = await response.json();
          setMicroagents(data);
        }
      } catch (error) {
        // Log error silently
      } finally {
        setLoading(false);
      }
    };

    fetchMicroagents();
  }, []);

  // Filter microagents based on the query
  useEffect(() => {
    if (!query || query === "/") {
      setFilteredMicroagents(microagents);
    } else {
      const searchTerm = query.slice(1).toLowerCase();
      const filtered = microagents.filter(
        (agent) =>
          agent.trigger.toLowerCase().includes(searchTerm) ||
          agent.name.toLowerCase().includes(searchTerm),
      );
      setFilteredMicroagents(filtered);
    }
  }, [query, microagents]);

  if (!isVisible || (filteredMicroagents.length === 0 && !loading)) {
    return null;
  }

  return (
    <div
      className={cn(
        "absolute bottom-full left-0 w-full max-h-60 overflow-y-auto bg-neutral-800 rounded-md shadow-lg z-10 mb-1 border border-neutral-600",
        className,
      )}
    >
      {loading && (
        <div className="p-2 text-neutral-400">Loading microagents...</div>
      )}
      {!loading && filteredMicroagents.length === 0 && (
        <div className="p-2 text-neutral-400">No microagents found</div>
      )}
      {!loading && filteredMicroagents.length > 0 && (
        <ul className="py-1">
          {filteredMicroagents.map((agent) => (
            <div
              key={agent.trigger}
              className="px-3 py-2 hover:bg-neutral-700 cursor-pointer flex flex-col"
              onClick={() => onSelect(agent.trigger)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  onSelect(agent.trigger);
                }
              }}
            >
              <span className="font-medium text-white">{agent.trigger}</span>
              <span className="text-xs text-neutral-400 truncate">
                {agent.description}
              </span>
            </div>
          ))}
        </ul>
      )}
    </div>
  );
}
