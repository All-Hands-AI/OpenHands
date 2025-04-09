import { RootState } from "#/store";
import ObservationType from "#/types/observation-type";
import { Slider } from "@heroui/react";
import { useEffect, useRef, useState } from "react";
import { LuCompass, LuStepBack, LuStepForward } from "react-icons/lu";
import { useSelector } from "react-redux";
import EditorContent from "./EditorContent";
import TaskProgress from "./TaskProgress";

const EditorNotification = () => {
  return (
    <div className="flex max-w-md items-center rounded-lg p-3">
      <div className="bg-gray-200 rounded-md p-2">
        <LuCompass size={16} />
      </div>
      <div className="text-14 ml-3">
        <p className="text-neutral-2">
          Thesis is using <span className="text-mercury-900">Browsing</span>
        </p>
        {/* <p className="bg-mercury-70 border-mercury-100 mt-1 rounded-full border px-2 py-1 text-gray-950">
          Distill is using{" "}
          <p className="mt-1 inline-block rounded-md px-2 py-1 text-gray-300">
            Browsing
          </p>
        </p> */}
      </div>
    </div>
  );
};

const ThesisComputer = () => {
  const isViewDrawer = true;
  const { computerList } = useSelector((state: RootState) => state.computer);
  console.log("🚀 ~ ThesisComputer ~ computerList:", computerList);

  const scrollRef = useRef<HTMLDivElement>(null);

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
    <div className=" flex w-full h-full flex-col overflow-y-auto  border bg-white p-4">
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
      <EditorNotification />

      <div className="bg-mercury-30 border-neutral-2 mb-3 flex h-[82%] w-full flex-1 flex-col rounded-2xl border">
        <div className="flex-1 overflow-y-auto px-4 py-2 w-full h-full">
          {computerList.length > 0 &&
            computerList.map((computerItem, index) => {
              if (index !== currentStep) return null;

              if (
                computerItem.observation === ObservationType.EDIT ||
                computerItem.observation === ObservationType.READ
              ) {
                return <EditorContent computerItem={computerItem} />;
              }

              return <div />;
            })}
          <div ref={scrollRef} />
        </div>

        <div className="border-t-neutral-2 flex h-11 w-full items-center gap-2 rounded-b-2xl border-t bg-white px-4">
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
