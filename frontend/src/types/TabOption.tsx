enum TabOption {
  PLANNER = "planner",
  CODE = "code",
  BROWSER = "browser",
}

type TabType = TabOption.PLANNER | TabOption.CODE | TabOption.BROWSER;

const AllTabs = [TabOption.PLANNER, TabOption.CODE, TabOption.BROWSER];

export { AllTabs, TabOption, type TabType };
