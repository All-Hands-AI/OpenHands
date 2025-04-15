import { RootState } from "#/store"
import { AgentState } from "#/types/agent-state"
import { LuCheck } from "react-icons/lu"
import { useSelector } from "react-redux"

const Stepper = () => {
  const steps = ["Starting Up", "Research & Execution", "Wrapping Up"]
  const { curAgentState } = useSelector((state: RootState) => state.agent)

  const getCurrentStep = () => {
    switch (curAgentState) {
      case AgentState.LOADING || AgentState.INIT:
        return 1

      case AgentState.RUNNING:
        return 2

      case AgentState.AWAITING_USER_INPUT:
        return 4

      default:
        return 3
    }
  }

  return (
    <div className="mb-4 flex w-full items-center justify-center rounded-[20px] bg-white">
      <div className="relative mx-auto flex w-full max-w-xl items-center justify-between py-6">
        {steps.map((label, i) => {
          const step = i + 1
          const isActive = step === getCurrentStep()
          const isCompleted = step < getCurrentStep()

          return (
            <div
              key={label}
              className="relative flex flex-1 flex-col items-center"
            >
              {i < steps.length - 1 && (
                <div className="absolute left-1/2 top-4 z-10 h-0.5 w-full bg-[#E6E6E6]" />
              )}

              <div
                className="z-10 flex h-8 w-8 items-center justify-center rounded-full bg-[#E6E6E6] font-bold text-black aria-checked:bg-[#92E54C] aria-selected:bg-white"
                aria-selected={isActive}
                aria-checked={isCompleted}
              >
                {isActive ? (
                  <div className="h-full w-full animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                ) : isCompleted ? (
                  <LuCheck />
                ) : (
                  step
                )}
              </div>

              {isActive ? (
                <div className="animate-gradient-smooth mt-2 bg-gradient-to-r from-[#FFFF] via-[#AFAFAF] to-[#0f0f0f] bg-[length:300%_100%] bg-clip-text text-sm font-bold text-transparent">
                  {label}
                </div>
              ) : (
                <span className="mt-2 text-center text-sm">{label}</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Stepper
