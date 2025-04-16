import { useSaveSettings } from "#/hooks/mutation/use-save-settings"
import { useSettings } from "#/hooks/query/use-settings"
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers"
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message"
import {
  useConversationActions,
  useGetConversationState,
} from "#/zutand-stores/coin/selector"
import { useGetJwt } from "#/zutand-stores/persist-config/selector"
import { Autocomplete, AutocompleteItem } from "@heroui/react"
import { ReactNode, useEffect, useState } from "react"
import { twMerge } from "tailwind-merge"
import { useAccount } from "wagmi"
import { OptionalTag } from "./optional-tag"

interface AgentSettingsDropdownInputProps {
  testId: string
  label: ReactNode
  name: string
  items: { key: React.Key; label: string }[]
  showOptionalTag?: boolean
  isDisabled?: boolean
  defaultSelectedKey?: string
  isClearable?: boolean
  className?: string
}

export function AgentSettingsDropdownInput({
  testId,
  label,
  name,
  items,
  showOptionalTag,
  isDisabled,
  defaultSelectedKey,
  isClearable,
  className = "",
}: AgentSettingsDropdownInputProps) {
  const agent = useGetConversationState("agent")
  const { handleSetAgent } = useConversationActions()
  const [agentValue, setAgentValue] = useState<string | null>(
    defaultSelectedKey,
  )
  const { data: settings } = useSettings()
  const { mutate: saveSettings } = useSaveSettings()
  const { isConnected } = useAccount()
  const jwt = useGetJwt()

  const isLoginStatus = isConnected && jwt

  useEffect(() => {
    if (agent) {
      console.log("settings:AGENT", agent)
      setAgentValue(agent)
      handleSetAgent(null)
    }
  }, [agent])

  useEffect(() => {
    if (settings) {
      setAgentValue(settings?.AGENT)
    }
  }, [settings, isLoginStatus])

  return (
    <label
      className={twMerge("mt-2 flex w-fit cursor-pointer gap-2", className)}
    >
      <div className="flex items-center gap-1">
        <span className="text-[14px] font-medium text-neutral-700 dark:text-[#595B57]">
          {label}:
        </span>
        {showOptionalTag && <OptionalTag />}
      </div>
      <Autocomplete
        aria-label={typeof label === "string" ? label : name}
        data-testid={testId}
        name={name}
        defaultItems={items}
        selectedKey={agentValue}
        // defaultSelectedKey={defaultSelectedKey}
        isClearable={isClearable}
        value={agentValue}
        onSelectionChange={(val) => {
          const oldValue = agentValue
          if (val && items.find((item) => item.key === val.toString())) {
            setAgentValue(val.toString())
            saveSettings(
              {
                ...settings,
                AGENT: val.toString(),
              },
              {
                onSuccess: () => {
                  displaySuccessToast("Update agent success!")
                },
                onError: (error) => {
                  const errorMessage = retrieveAxiosErrorMessage(error)
                  displayErrorToast(errorMessage)
                },
              },
            )
          } else {
            setAgentValue(oldValue)
          }
        }}
        isDisabled={isDisabled}
        className="w-full"
        classNames={{
          popoverContent:
            "bg-white dark:bg-[#1E1E1F] rounded-xl border border-neutral-1000 dark:border-[#232521] text-[14px] font-medium text-neutral-100 dark:text-[#EFEFEF]",
        }}
        inputProps={{
          classNames: {
            inputWrapper:
              "bg-white dark:bg-[#1E1E1F] border border-neutral-1000 dark:border-[#232521] w-full rounded-lg px-2 py-1 placeholder:italic",
            input:
              "font-x text-[14px] font-medium text-neutral-100 dark:text-[#EFEFEF]",
          },
        }}
        listboxProps={{
          itemClasses: {
            base: [
              "data-[hover=true]:bg-neutral-1000",
              "data-[selectable=true]:focus:bg-neutral-1000",
            ],
          },
        }}
      >
        {(item) => (
          <AutocompleteItem key={item.key}>{item.label}</AutocompleteItem>
        )}
      </Autocomplete>
    </label>
  )
}
