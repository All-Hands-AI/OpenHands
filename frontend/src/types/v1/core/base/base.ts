type EventType =
  | "MCPTool"
  | "Finish"
  | "Think"
  | "ExecuteBash"
  | "FileEditor"
  | "StrReplaceEditor"
  | "TaskTracker";

type ActionOnlyType =
  | "BrowserNavigate"
  | "BrowserClick"
  | "BrowserType"
  | "BrowserGetState"
  | "BrowserGetContent"
  | "BrowserScroll"
  | "BrowserGoBack"
  | "BrowserListTabs"
  | "BrowserSwitchTab"
  | "BrowserCloseTab";

type ObservationOnlyType = "Browser";

type ActionEventType = `${ActionOnlyType}Action` | `${EventType}Action`;
type ObservationEventType =
  | `${ObservationOnlyType}Observation`
  | `${EventType}Observation`;

export interface ActionBase<T extends ActionEventType = ActionEventType> {
  kind: T;
}

export interface ObservationBase<
  T extends ObservationEventType = ObservationEventType,
> {
  kind: T;
}
