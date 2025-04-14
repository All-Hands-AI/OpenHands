export const Stepper = ({ currentStep }) => {
  const steps = ["Starting Up", "Research & Execution", "Wrapping Up"]

  return (
    <div className="relative mx-auto flex w-full max-w-xl items-center justify-between py-6">
      {steps.map((label, i) => {
        const step = i + 1
        const isActive = step === currentStep
        const isCompleted = step < currentStep

        return (
          <div
            key={label}
            className="relative flex flex-1 flex-col items-center"
          >
            {i < steps.length - 1 && (
              <div className="absolute left-1/2 top-4 z-10 h-0.5 w-full bg-[#E6E6E6]" />
            )}

            <div className="z-10 flex h-8 w-8 items-center justify-center rounded-full bg-[#E6E6E6] font-bold text-black">
              {isActive ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
              ) : (
                step
              )}
            </div>
            <span className="mt-2 text-center text-sm">{label}</span>
          </div>
        )
      })}
    </div>
  )
}
