import { useSaveSettings } from "#/hooks/mutation/use-save-settings"
import { useSettings } from "#/hooks/query/use-settings"
import StarIcon from "#/icons/star-icons.svg?react"
import { useCasesMocks } from "#/mocks/use-cases.mock"
import { displayErrorToast } from "#/utils/custom-toast-handlers"
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message"
import {
  useConversationActions,
  useGetConversationState,
} from "#/zutand-stores/coin/selector"

export function SampleMsg() {
  const initMsg = useGetConversationState("initMsg")
  const { handleSetInitMsg, handleSetAgent } = useConversationActions()
  console.log("initMsg", initMsg)
  const { data: settings } = useSettings()
  const { mutate: saveSettings } = useSaveSettings()

  if (!settings) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        Loading...
      </div>
    )
  }

  return (
    <div className="mt-3 grid w-full grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-2">
      {Object.entries(useCasesMocks).map(([k, itemValue], key) => {
        const titleQuestion = itemValue.find((x: any) => x.source === "user")

        return (
          <button
            className="cursor-pointer rounded-[12px] border border-neutral-1000 bg-transparent bg-white p-5 transition-all duration-150 ease-in hover:scale-105 hover:shadow-md"
            key={key}
            onClick={() => {
              handleSetInitMsg(titleQuestion.message)
              handleSetAgent(key ? "DummyAgent" : "CodeActAgent")
              saveSettings(
                {
                  ...settings,
                  AGENT: key ? "DummyAgent" : "CodeActAgent",
                },
                {
                  onSuccess: () => {
                    console.log("settings: update settings success")
                  },
                  onError: (error) => {
                    const errorMessage = retrieveAxiosErrorMessage(error)
                    displayErrorToast(errorMessage)
                  },
                },
              )
            }}
          >
            <StarIcon className="mb-5" />
            <span className="mb-2 flex gap-2 text-[16px] font-medium text-neutral-100">
              {titleQuestion.message.slice(0, 10).toUpperCase()}
            </span>
            <p className="line-clamp-3 text-left text-[16px] text-neutral-700">
              {titleQuestion.message}
            </p>
          </button>
        )
      })}
    </div>
  )
}
