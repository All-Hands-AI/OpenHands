enum TabOption {
  PLANNER = "planner",
  CODE = "code",
  BROWSER = "browser",
  JUPYTER = "jupyter",
}

type TabType =
  | TabOption.PLANNER
  | TabOption.CODE
  | TabOption.BROWSER
  | TabOption.JUPYTER;

const AllTabs = [
  TabOption.CODE,
  TabOption.BROWSER,
  TabOption.PLANNER,
  TabOption.JUPYTER,
];

export { AllTabs, TabOption, type TabType };
