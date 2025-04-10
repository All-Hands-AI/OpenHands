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
    <div className="mt-6 grid w-full grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-2">
      {Object.entries(useCasesMocks).map(([k, itemValue], key) => {
        const titleQuestion = itemValue.find((x: any) => x.source === "user")

        return (
          <button
            className="cursor-pointer rounded-[12px] border border-gray-200 bg-transparent p-6 transition-all duration-150 ease-in hover:scale-105 hover:shadow-md"
            key={key}
            onClick={() => {
              console.log("first", titleQuestion.message)
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
            <StarIcon className="mb-6" />
            <div className="mb-4 flex gap-2">
              {titleQuestion.message.slice(0, 10).toUpperCase()}
            </div>
            <div className="text-left text-[16px] font-semibold text-tertiary">
              {titleQuestion.message}
            </div>
          </button>
        )
      })}
    </div>
  )
}
