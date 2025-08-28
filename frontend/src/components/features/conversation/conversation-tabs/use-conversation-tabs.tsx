import {
  createContext,
  Dispatch,
  PropsWithChildren,
  SetStateAction,
  useContext,
  useMemo,
  useState,
} from "react";

export type ConversationTab =
  | "editor"
  | "browser"
  | "jupyter"
  | "served"
  | "vscode";

export type TerminalTab = "terminal";

type ConversationTabsContext = [
  {
    selectedTab: ConversationTab | null;
    terminalOpen: boolean;
  },
  {
    onTabChange(value: ConversationTab | null): void;
    onTerminalChange: Dispatch<SetStateAction<boolean>>;
  },
];
export const ConversationTabContext = createContext<
  ConversationTabsContext | undefined
>(undefined);

export function ConversationTabProvider({ children }: PropsWithChildren) {
  const [selectedTab, onTabChange] = useState<ConversationTab | null>("editor");
  const [terminalOpen, onTerminalChange] = useState<boolean>(false);

  const state = useMemo<ConversationTabsContext>(
    () => [
      { selectedTab, terminalOpen },
      { onTabChange, onTerminalChange },
    ],
    [selectedTab, terminalOpen],
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
