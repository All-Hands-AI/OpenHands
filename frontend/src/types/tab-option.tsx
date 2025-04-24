enum TabOption {
  PLANNER = "planner",
  CODE = "code",
  BROWSER = "browser",
  JUPYTER = "jupyter",
  VSCODE = "vscode",
}

type TabType =
  | TabOption.PLANNER
  | TabOption.CODE
  | TabOption.BROWSER
  | TabOption.JUPYTER
  | TabOption.VSCODE;

const AllTabs = [
  TabOption.CODE,
  TabOption.VSCODE,
  TabOption.BROWSER,
  TabOption.PLANNER,
  TabOption.JUPYTER,
];

export { AllTabs, TabOption, type TabType };
