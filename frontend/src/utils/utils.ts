import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface EventActionHistory {
  args?: {
    LLM_API_KEY?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export const removeApiKey = (
  data: EventActionHistory[],
): EventActionHistory[] =>
  data.map((item, index, array) => {
    // Create a shallow copy of item
    const newItem = { ...item };

    // Check if LLM_API_KEY exists and delete it from a new args object
    if (newItem.args?.LLM_API_KEY) {
      const currentModel = newItem.args.model as string | undefined;
      const previousModel =
        index > 0
          ? (array[index - 1].args?.model as string | undefined)
          : undefined;

      if (currentModel && previousModel) {
        const [currentModelBase] = currentModel.split("/");
        const [previousModelBase] = previousModel.split("/");

        if (currentModelBase !== previousModelBase) {
          const newArgs = { ...newItem.args };
          delete newArgs.LLM_API_KEY;
          newItem.args = newArgs;
        }
      } else {
        const newArgs = { ...newItem.args };
        delete newArgs.LLM_API_KEY;
        newItem.args = newArgs;
      }
    }

    return newItem;
  });
