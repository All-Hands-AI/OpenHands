import React, { use, useEffect } from "react"
import { useNavigation } from "react-router"
import { useDispatch, useSelector } from "react-redux"
import { RootState } from "#/store"
import { addFile, removeFile } from "#/state/initial-query-slice"
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64"
import { ChatInput } from "#/components/features/chat/chat-input"
import { cn } from "#/utils/utils"
import AttachImageLabel from "../../icons/attach-icon.svg?react"
import { ImageCarousel } from "../features/images/image-carousel"
import { UploadImageInput } from "../features/images/upload-image-input"
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation"
import { LoadingSpinner } from "./loading-spinner"
import { useGetConversationState } from "#/zutand-stores/coin/selector"

interface TaskFormProps {
  ref: React.RefObject<HTMLFormElement | null>
}

export function TaskForm({ ref }: TaskFormProps) {
  const dispatch = useDispatch()
  const navigation = useNavigation()
  const initMsg = useGetConversationState("initMsg")

  const { files } = useSelector((state: RootState) => state.initialQuery)

  const [text, setText] = React.useState("")
  const [inputIsFocused, setInputIsFocused] = React.useState(false)
  const { mutate: createConversation, isPending } = useCreateConversation()

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    const q = formData.get("q")?.toString()
    createConversation({ q })
  }

  useEffect(() => {
    if (initMsg) {
      setText(initMsg)
    }
  }, [initMsg])

  return (
    <div className="flex w-full flex-col gap-1">
      <form
        ref={ref}
        onSubmit={handleSubmit}
        className="flex flex-col items-center gap-2"
      >
        <div
          className={cn(
            "w-full rounded-xl px-3 text-[16px] leading-5 transition-colors duration-200",
            inputIsFocused
              ? "bg-white dark:bg-[#171717]"
              : "bg-white dark:bg-[#171717]",
          )}
        >
          {isPending ? (
            <div className="flex justify-center py-3">
              <LoadingSpinner size="small" />
            </div>
          ) : (
            <div className="relative">
              <ChatInput
                name="q"
                onSubmit={() => {
                  if (typeof ref !== "function") ref?.current?.requestSubmit()
                }}
                onChange={(message) => setText(message)}
                onFocus={() => setInputIsFocused(true)}
                onBlur={() => setInputIsFocused(false)}
                onImagePaste={async (imageFiles) => {
                  const promises = imageFiles.map(convertImageToBase64)
                  const base64Images = await Promise.all(promises)
                  base64Images.forEach((base64) => {
                    dispatch(addFile(base64))
                  })
                }}
                value={text}
                maxRows={15}
                showButton={!!text}
                className="bg-white py-3 pl-8 text-[16px] leading-5 text-neutral-100 placeholder:text-[#979995] dark:bg-[#171717]"
                buttonClassName="pb-[8px] "
                disabled={navigation.state === "submitting"}
              />
              <div className="absolute left-[-2px] top-1/2 -translate-y-1/2">
                <UploadImageInput
                  onUpload={async (uploadedFiles) => {
                    const promises = uploadedFiles.map(convertImageToBase64)
                    const base64Images = await Promise.all(promises)
                    base64Images.forEach((base64) => {
                      dispatch(addFile(base64))
                    })
                  }}
                  label={<AttachImageLabel className="text-neutral-100" />}
                />
              </div>
            </div>
          )}
        </div>
      </form>
      {files.length > 0 && (
        <ImageCarousel
          size="large"
          images={files}
          onRemove={(index) => dispatch(removeFile(index))}
        />
      )}
    </div>
  )
}
