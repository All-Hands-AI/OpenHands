enum TabOption {
  PLANNER = "planner",
  BROWSER = "browser",
  JUPYTER = "jupyter",
  VSCODE = "vscode",
}

type TabType =
  | TabOption.PLANNER
  | TabOption.BROWSER
  | TabOption.JUPYTER
  | TabOption.VSCODE;

const AllTabs = [
  TabOption.VSCODE,
  TabOption.BROWSER,
  TabOption.PLANNER,
  TabOption.JUPYTER,
];

export { AllTabs, TabOption, type TabType };
