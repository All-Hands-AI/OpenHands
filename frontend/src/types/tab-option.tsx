enum TabOption {
  STATUS = "status",
  PLANNER = "planner",
  BROWSER = "browser",
  JUPYTER = "jupyter",
  VSCODE = "vscode",
}

type TabType =
  | TabOption.STATUS
  | TabOption.PLANNER
  | TabOption.BROWSER
  | TabOption.JUPYTER
  | TabOption.VSCODE;

const AllTabs = [
  TabOption.STATUS,
  TabOption.VSCODE,
  TabOption.BROWSER,
  TabOption.PLANNER,
  TabOption.JUPYTER,
];

export { AllTabs, TabOption, type TabType };
