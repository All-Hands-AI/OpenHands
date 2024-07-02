enum TabOption {
  PLANNER = "planner",
  CODE = "code",
  BROWSER = "browser",
  JUPYTER = "jupyter",
  INVARIANT = "invariant",
}

type TabType =
  | TabOption.PLANNER
  | TabOption.CODE
  | TabOption.BROWSER
  | TabOption.JUPYTER
  | TabOption.INVARIANT;

const AllTabs = [
  TabOption.CODE,
  TabOption.BROWSER,
  TabOption.PLANNER,
  TabOption.JUPYTER,
  TabOption.INVARIANT,
];

export { AllTabs, TabOption, type TabType };
