import { useQuery } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useRuntimeIsReady } from "#/hooks/use-runtime-is-ready";

interface Task {
  id: string;
  title: string;
  status: "todo" | "in_progress" | "done";
  notes?: string;
}

const parseTasksFromMarkdown = (content: string): Task[] => {
  const tasks: Task[] = [];
  const lines = content.split("\n");

  let currentTask: Partial<Task> | null = null;

  for (const line of lines) {
    // Match task lines like: "1. ✅ Add 'tasks' to ConversationTab type in conversation-slice.tsx"
    const taskMatch = line.match(/^(\d+)\.\s*([✅🔄⏳])\s*(.+)$/u);
    if (taskMatch) {
      // Save previous task if exists
      if (
        currentTask &&
        currentTask.id &&
        currentTask.title &&
        currentTask.status
      ) {
        tasks.push(currentTask as Task);
      }

      const [, id, statusIcon, title] = taskMatch;
      let status: Task["status"] = "todo";

      // Determine status from emoji
      if (statusIcon === "✅") {
        status = "done";
      } else if (statusIcon === "🔄") {
        status = "in_progress";
      } else if (statusIcon === "⏳") {
        status = "todo";
      }

      currentTask = {
        id,
        title: title.trim(),
        status,
        notes: "",
      };
    } else if (currentTask && line.trim() && !line.startsWith("#")) {
      // This is likely a notes line for the current task
      if (currentTask.notes) {
        currentTask.notes += ` ${line.trim()}`;
      } else {
        currentTask.notes = line.trim();
      }
    }
  }

  // Don't forget the last task
  if (
    currentTask &&
    currentTask.id &&
    currentTask.title &&
    currentTask.status
  ) {
    tasks.push(currentTask as Task);
  }

  return tasks;
};

export const useGetTasks = () => {
  const { conversationId } = useConversationId();
  const runtimeIsReady = useRuntimeIsReady();

  return useQuery({
    queryKey: ["tasks", conversationId],
    queryFn: async () => {
      try {
        const content = await ConversationService.getFile(
          conversationId,
          "TASKS.md",
        );
        return parseTasksFromMarkdown(content);
      } catch (error) {
        // If TASKS.md doesn't exist, return empty array
        return [];
      }
    },
    retry: false,
    staleTime: 1000 * 30, // 30 seconds
    gcTime: 1000 * 60 * 5, // 5 minutes
    enabled: runtimeIsReady && !!conversationId,
    meta: {
      disableToast: true,
    },
  });
};
