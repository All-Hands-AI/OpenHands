enum TabOption {
  PLANNER = "planner",
  CODE = "code",
  BROWSER = "browser",
  JUPYTER = "jupyter",
  APP = "app",
}

type TabType =
  | TabOption.PLANNER
  | TabOption.CODE
  | TabOption.BROWSER
  | TabOption.JUPYTER
  | TabOption.APP;

const AllTabs = [
  TabOption.CODE,
  TabOption.BROWSER,
  TabOption.PLANNER,
  TabOption.JUPYTER,
  TabOption.APP,
];

export { AllTabs, TabOption, type TabType };
