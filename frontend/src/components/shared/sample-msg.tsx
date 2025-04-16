import { useSaveSettings } from "#/hooks/mutation/use-save-settings"
import { useSettings } from "#/hooks/query/use-settings"
import StarIcon from "#/icons/star-icons.svg?react"
import { useCasesMocks } from "#/mocks/use-cases.mock"
import { displayErrorToast } from "#/utils/custom-toast-handlers"
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message"
import { useConversationActions } from "#/zutand-stores/coin/selector"
import { useGetJwt } from "#/zutand-stores/persist-config/selector"
import { useAccount } from "wagmi"

export function SampleMsg() {
  const { handleSetInitMsg, handleSetAgent } = useConversationActions()
  const { data: settings } = useSettings()
  const { mutate: saveSettings } = useSaveSettings()
  const { isConnected } = useAccount()
  const jwt = useGetJwt()

  const isUserLoggedIn = !!jwt && !!isConnected

  // if (!settings) {
  //   return (
  //     <div className="mt-3 grid w-full grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-2">
  //       <div className="h-[200px] animate-pulse rounded-[12px] border-neutral-1000 bg-white"></div>
  //       <div className="h-[200px] animate-pulse rounded-[12px] border-neutral-1000 bg-white"></div>
  //     </div>
  //   )
  // }

  return (
    <div className="mt-3 grid w-full grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-2">
      {useCasesMocks.map((itemValue, key) => {
        const { agent } = itemValue
        return (
          <button
            type="button"
            className="cursor-pointer rounded-[12px] border border-neutral-1000 bg-white p-5 transition-all duration-150 ease-in hover:scale-105 hover:shadow-md"
            key={key}
            onClick={() => {
              if (!isUserLoggedIn) {
                return
              }

              handleSetInitMsg(itemValue.prompt)
              handleSetAgent(agent)
              // TODO: enable later
              saveSettings(
                {
                  ...settings,
                  AGENT: agent,
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
              {itemValue.title}
            </span>
            <p className="line-clamp-3 text-left text-[16px] text-neutral-700">
              {itemValue.prompt.slice(0, 100)}
            </p>
          </button>
        )
      })}
    </div>
  )
}
