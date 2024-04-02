enum TabOption {
  TERMINAL = "terminal",
  PLANNER = "planner",
  CODE = "code",
  BROWSER = "browser",
}

type TabType =
  | TabOption.TERMINAL
  | TabOption.PLANNER
  | TabOption.CODE
  | TabOption.BROWSER;

const AllTabs = [
  TabOption.TERMINAL,
  TabOption.PLANNER,
  TabOption.CODE,
  TabOption.BROWSER,
];

export { AllTabs, TabOption, type TabType };
