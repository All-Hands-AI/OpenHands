import {
  LuCheck,
  LuChevronDown,
  LuChevronUp,
  LuCircleDashed,
  LuClock,
} from "react-icons/lu"
// import parseJson from "parse-json";
import { useState } from "react"

const STEP_STATUSES = {
  COMPLETED: "completed",
  IN_PROGRESS: "in_progress",
  NOT_STARTED: "not_started",
}

const TaskProgress = () => {
  const [isFinalizeCollapsed, setIsFinalizeCollapsed] = useState(true)
  const tasksProgress = {}

  const mapStatusToIcon = {
    [STEP_STATUSES.COMPLETED]: <LuCheck color="#008000" width={18} />,
    [STEP_STATUSES.IN_PROGRESS]: (
      <LuCircleDashed className="animate-spin" width={18} />
    ),
    [STEP_STATUSES.NOT_STARTED]: <LuClock width={18} />,
  } as any

  const taskProgressContent =
    // @ts-ignore
    tasksProgress?.content && JSON.parse(tasksProgress.content)

  const taskSteps = taskProgressContent?.steps
  const taskStatus = taskProgressContent?.step_statuses

  const isTaskStatus = taskStatus && Array.isArray(taskStatus)
  const isTaskSteps = taskSteps && Array.isArray(taskSteps)

  const taskInProgress =
    isTaskStatus &&
    taskStatus.find((task: any) => task === STEP_STATUSES.IN_PROGRESS)

  const taskInProgressIndex =
    isTaskStatus && taskInProgress && taskStatus.indexOf(taskInProgress)

  const isTaskInProgress =
    isTaskStatus && taskStatus.includes(STEP_STATUSES.IN_PROGRESS)

  const taskStepInProgress = isTaskSteps && taskSteps?.[taskInProgressIndex]
  const lastTaskCompleted = isTaskSteps && taskSteps?.[taskSteps.length - 1]

  const toggleFinalizeCollapsed = () => {
    setIsFinalizeCollapsed(!isFinalizeCollapsed)
  }

  return (
    <div className=" z-50 flex min-h-[30px] w-full items-center rounded-[12px] px-4 py-2 bg-[#F3F3F1] relative">
      {isFinalizeCollapsed ? (
        <div className="flex w-full items-start justify-between">
          <div className="animate-slide-up flex gap-2 transition-all duration-300">
            {!!isTaskInProgress ? (
              <LuCircleDashed className="animate-spin" width={18} />
            ) : (
              <LuCheck color="#008000" width={18} />
            )}
            <div className="flex max-w-[500px] flex-col">
              <span className="text-mercury-950 text-14 truncate font-semibold">
                {!!isTaskInProgress ? taskStepInProgress : lastTaskCompleted}
              </span>
              {!!isTaskInProgress && (
                <span className="text-mercury-900 text-12">Thinking</span>
              )}
            </div>
          </div>
          <div
            className="flex cursor-pointer items-center gap-1"
            onClick={() => toggleFinalizeCollapsed()}
          >
            <span className="text-mercury-900 text-13 font-medium">
              {isTaskInProgress
                ? taskInProgressIndex > 0
                  ? taskInProgressIndex
                  : taskInProgressIndex + 1
                : taskStatus?.length}
              /{taskStatus?.length}
            </span>
            <LuChevronUp className="h-5 w-5" />
          </div>
        </div>
      ) : (
        <div className="border-neutral-1000 absolute right-0 bottom-0 flex h-[300px] flex-col rounded-[12px] border bg-white px-3 py-2 w-full">
          <div className="flex items-start justify-between">
            <span className="text-mercury-950 text-16 mb-2 font-bold">
              Task progress
            </span>
            <div
              className="flex cursor-pointer items-center gap-1"
              onClick={() => toggleFinalizeCollapsed()}
            >
              <span className="text-mercury-900 text-13 font-medium">
                {isTaskInProgress
                  ? taskInProgressIndex > 0
                    ? taskInProgressIndex
                    : taskInProgressIndex + 1
                  : taskStatus?.length}
                /{taskStatus?.length}
              </span>
              <LuChevronDown className="h-5 w-5" />
            </div>
          </div>
          <div className="max-h-[min(calc(100vh-200px),400px)] overflow-y-auto">
            <div className="pb-2">
              <div className="flex gap-2">
                <div>
                  {isTaskStatus &&
                    taskStatus?.map((status: any) => {
                      return (
                        <div key={status} className="h-8">
                          {mapStatusToIcon?.[status]}
                        </div>
                      )
                    })}
                </div>
                <div>
                  {isTaskSteps &&
                    taskSteps?.map((step: any, index: number) => {
                      return (
                        <div className="h-8">
                          <span className="text-mercury-950 text-14 font-medium">
                            {step}
                          </span>
                        </div>
                      )
                    })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TaskProgress
