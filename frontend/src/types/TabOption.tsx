enum TabOption {
  PLANNER = "planner",
  CODE = "code",
  BROWSER = "browser",
  JUPYTER = "jupyter",
  SECURITY = "security",
}

type TabType =
  | TabOption.PLANNER
  | TabOption.CODE
  | TabOption.BROWSER
  | TabOption.JUPYTER
  | TabOption.SECURITY;

const AllTabs = [
  TabOption.CODE,
  TabOption.BROWSER,
  TabOption.PLANNER,
  TabOption.JUPYTER,
  TabOption.SECURITY,
];

export { AllTabs, TabOption, type TabType };
