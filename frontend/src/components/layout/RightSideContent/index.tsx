import { BrowserPanel } from "#/components/features/browser/browser";
import { useSettings } from "#/hooks/query/use-settings";
import TerminalPage from "#/routes/_oh.app.terminal";
import { RootState } from "#/store";
import ObservationType from "#/types/observation-type";
import { Slider, useDisclosure } from "@heroui/react";
import { useEffect, useRef, useState } from "react";
import { LuSquareChartGantt, LuStepBack, LuStepForward } from "react-icons/lu";
import Markdown, { Components } from "react-markdown";
import { useSelector } from "react-redux";
import CodeView from "./CodeView";
import EditorContent from "./EditorContent";
import TaskProgress from "./TaskProgress";

const EditorNotification = () => {
  return (
    <div className="flex max-w-md items-center rounded-lg mb-3">
      <p className="text-[#666] font-medium">
        Thesis is using <span className="text-mercury-900">Browsing</span>
      </p>
      {/* <p className="bg-mercury-70 border-mercury-100 mt-1 rounded-full border px-2 py-1 text-gray-950">
          Distill is using{" "}
          <p className="mt-1 inline-block rounded-md px-2 py-1 text-gray-300">
            Browsing
          </p>
        </p> */}
    </div>
  );
};

const ThesisComputer = () => {
  const isViewDrawer = true;
  const { computerList } = useSelector((state: RootState) => state.computer);
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  console.log("🚀 ~ ThesisComputer ~ curAgentState:", curAgentState);

  const scrollRef = useRef<HTMLDivElement>(null);
  const { data: settings } = useSettings();

  const [currentStep, setCurrentStep] = useState(0);
  const totalSteps = computerList.length;
  const [sliderValue, setSliderValue] = useState(0);

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

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

  const components: Partial<Components> = {
    ol: ({ children }) => (
      <ol style={{ listStyleType: "decimal", paddingLeft: "16px" }}>
        {children}
      </ol>
    ),
    li: ({ children }) => {
      return <li className="text-[14px]">{children}</li>;
    },
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    ),
    p: ({ children }) => <p className="text-[14px]">{children}</p>,
    h1: ({ children }) => <h1 className="text-[14px]">{children}</h1>,
    h2: ({ children }) => <h2 className="text-[14px]">{children}</h2>,
    h3: ({ children }) => <h3 className="text-[14px]">{children}</h3>,
    h4: ({ children }) => <h4 className="text-[14px]">{children}</h4>,
    h5: ({ children }) => <h5 className="text-[14px]">{children}</h5>,
    h6: ({ children }) => <h6 className="text-[14px]">{children}</h6>,
  };

  const toPascalCase = (str: string) => {
    return str
      .split("_")
      .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  console.log('computerList', computerList)

  const renderToolCalls = (toolCalls: any) => {
    const nameValue = toolCalls?.function?.name;
    const results = toolCalls?.results;

    return (
      <div>
        <div className="mb-2 flex items-center justify-center gap-1 border-b-[1px] pb-2">
          <LuSquareChartGantt size={20} />
          <span className="text-neutral-1 text-16 font-bold">
            {nameValue === "final_answer"
              ? "Step Answer"
              : toPascalCase(nameValue)}
          </span>
        </div>

        <div className="mb-2">
          {results &&
            Array.isArray(results) &&
            results.length > 0 &&
            results.map((result, index) => {
              if (result.dtype === "text") {
                return (
                  <div key={index} className="gap-2">
                    <Markdown components={components}>
                      {result.content}
                    </Markdown>
                  </div>
                );
              }
              return <span key={index}>image</span>;
            })}
        </div>
      </div>
    );
  };

  return (
    <div className=" flex w-full h-full flex-col overflow-y-auto border border-neutral-1000 bg-white p-4 rounded-xl">
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

      <div className="bg-mercury-30 border-neutral-1000 mb-3 flex h-[82%] w-full flex-1 flex-col rounded-2xl border">
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

              // TODO: check type browse_interactive of observation
              if (computerItem.observation === ObservationType.BROWSE) {
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

        <div className="border-t-neutral-1000 flex h-11 w-full items-center gap-2 rounded-b-2xl border-t bg-white px-4">
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
