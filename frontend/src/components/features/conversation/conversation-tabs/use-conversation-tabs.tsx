import {
  createContext,
  PropsWithChildren,
  useContext,
  useMemo,
  useState,
} from "react";

export type ConversationTab =
  | "editor"
  | "browser"
  | "jupyter"
  | "served"
  | "vscode"
  | "terminal";

type ConversationTabsContext = [
  {
    selectedTab: ConversationTab | null;
  },
  {
    onTabChange(value: ConversationTab | null): void;
  },
];
export const ConversationTabContext = createContext<
  ConversationTabsContext | undefined
>(undefined);

export function ConversationTabProvider({ children }: PropsWithChildren) {
  const [selectedTab, onTabChange] = useState<ConversationTab | null>("editor");

  const state = useMemo<ConversationTabsContext>(
    () => [{ selectedTab }, { onTabChange }],
    [selectedTab],
  );

  return (
    <ConversationTabContext.Provider value={state}>
      {children}
    </ConversationTabContext.Provider>
  );
}

export const useConversationTabs = () => {
  const context = useContext(ConversationTabContext);

  if (!context) {
    throw new Error("Missing conversation tabs context");
  }

  return context;
};
