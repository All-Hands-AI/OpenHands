import { BrowserPanel } from "#/components/features/browser/browser";
import { useSettings } from "#/hooks/query/use-settings";
import TerminalPage from "#/routes/terminal-tab";
import { RootState } from "#/store";
import ObservationType from "#/types/observation-type";
import { Slider } from "@heroui/react";
import { useEffect, useRef, useState } from "react";
import { LuStepBack, LuStepForward } from "react-icons/lu";
import { useSelector } from "react-redux";
import CodeView from "./CodeView";
import EditorContent from "./EditorContent";
import TaskProgress from "./TaskProgress";

const ThesisComputer = () => {
  const isViewDrawer = true;
  const { computerList, eventID } = useSelector(
    (state: RootState) => state.computer
  );
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const scrollRef = useRef<HTMLDivElement>(null);
  const { data: settings } = useSettings();

  const [currentStep, setCurrentStep] = useState(0);
  const totalSteps = computerList.length;
  const [sliderValue, setSliderValue] = useState(0);

  const handleNextStep = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSliderChange = (value: number) => {
    setSliderValue(value);
    const step = Math.floor((value / 100) * (totalSteps - 1));
    setCurrentStep(step);
  };

  useEffect(() => {
    if (eventID && computerList.length > 0) {
      const matchingIndex = computerList.findIndex(
        (item) => item.cause === eventID
      );
      if (matchingIndex !== -1) {
        setCurrentStep(matchingIndex);
        const newSliderValue =
          totalSteps > 1 ? (matchingIndex / (totalSteps - 1)) * 100 : 0;
        setSliderValue(newSliderValue);
      }
    }
  }, [eventID, computerList, totalSteps]);

  // Add useEffect to handle auto progression
  useEffect(() => {
    if (computerList.length > currentStep) {
      const newStep = computerList.length - 1;
      setCurrentStep(newStep);
      // Calculate and set slider value based on new step
      const newSliderValue =
        totalSteps > 1 ? (newStep / (totalSteps - 1)) * 100 : 0;
      setSliderValue(newSliderValue);
    }
  }, [computerList, totalSteps]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [computerList]);

  if (!isViewDrawer) {
    return <div />;
  }

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto rounded-xl rounded-br-none rounded-tr-none border border-neutral-1000 bg-white p-4">
      <div className="flex items-center justify-between">
        <h4 className="text-neutral-1 text-18 font-semibold">Thesis</h4>
        {/* <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              className="h-6 w-6 cursor-pointer transition-all duration-300 hover:scale-110"
              onClick={() => toggleViewDistillComputer(!isViewDrawer)}
            >
              <CompressOutlined style={{ color: "#363636" }} />
            </button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Minimize</p>
          </TooltipContent>
        </Tooltip> */}
      </div>

      {computerList.length > 0 &&
        computerList.map((computerItem, index) => {
          const observation = computerItem?.observation;
          const mapObservationTypeToText = {
            [ObservationType.READ]: "Editor",
            [ObservationType.EDIT]: "Editor",
            [ObservationType.BROWSE]: "Browser",
            [ObservationType.BROWSER_MCP]: "Browser",
          };

          if (index !== currentStep) return null;
          return (
            <div className="mb-3 items-center rounded-lg">
              <p className="text-[14px] font-medium text-[#666]">
                Thesis is using{" "}
                <span className="font-semibold text-[#666]">
                  {mapObservationTypeToText[observation] || "Terminal"}
                </span>
              </p>
              <div className="mt-1 max-w-fit rounded-full bg-[#E6E6E6] px-3 py-1">
                <span className="text-[12px] font-medium text-[#0F0F0F]">
                  {computerItem?.message}
                </span>
              </div>
            </div>
          );
        })}

      <div className="bg-mercury-30 mb-3 flex h-[82%] w-full flex-1 flex-col rounded-2xl border border-neutral-1000">
        <div className="relative h-full w-full flex-1 overflow-y-auto px-4 py-2">
          {computerList.length > 0 &&
            computerList.map((computerItem, index) => {
              if (index !== currentStep) return null;

              if (
                computerItem.observation === ObservationType.EDIT ||
                computerItem.observation === ObservationType.READ
              ) {
                return <EditorContent computerItem={computerItem} />;
              }

              // TODO: check type browse_interactive of observation
              if (
                computerItem.observation === ObservationType.BROWSE ||
                computerItem.observation === ObservationType.BROWSER_MCP
              ) {
                return <BrowserPanel computerItem={computerItem} />;
              }

              if ([ObservationType.RUN].includes(computerItem.observation)) {
                return <TerminalPage />;
              }

              if (computerItem.observation === ObservationType.RUN_IPYTHON) {
                return <CodeView fileContent={computerItem.extras.code} />;
              }

              return <div />;
            })}
          <div ref={scrollRef} />
        </div>

        <div className="flex h-11 w-full items-center gap-2 rounded-b-2xl border-t border-t-neutral-1000 bg-white px-4">
          <div className="flex items-center gap-2">
            <div
              className={`cursor-pointer ${currentStep === 0 ? "opacity-50" : ""}`}
              onClick={handlePrevStep}
            >
              <LuStepBack width={18} color="#979995" />
            </div>
            <div
              className={`cursor-pointer ${currentStep === totalSteps - 1 ? "opacity-50" : ""}`}
              onClick={handleNextStep}
            >
              <LuStepForward width={18} color="#979995" />
            </div>
          </div>
          <Slider
            value={[Math.floor((currentStep / (totalSteps - 1)) * 100)]}
            onChange={(value) => handleSliderChange(value[0] ?? 0)}
            step={1}
            size="sm"
          />
        </div>
      </div>
      <TaskProgress />
    </div>
  );
};

export default ThesisComputer;
