import React from "react";
import { useNavigation } from "react-router";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "#/store";
import { addFile, removeFile } from "#/state/initial-query-slice";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { ChatInput } from "#/components/features/chat/chat-input";
import { cn } from "#/utils/utils";
import AttachImageLabel from "../../icons/attach-icon.svg?react";
import { ImageCarousel } from "../features/images/image-carousel";
import { UploadImageInput } from "../features/images/upload-image-input";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { LoadingSpinner } from "./loading-spinner";

interface TaskFormProps {
  ref: React.RefObject<HTMLFormElement | null>;
}

export function TaskForm({ ref }: TaskFormProps) {
  const dispatch = useDispatch();
  const navigation = useNavigation();

  const { files } = useSelector((state: RootState) => state.initialQuery);

  const [text, setText] = React.useState("");
  const [inputIsFocused, setInputIsFocused] = React.useState(false);
  const { mutate: createConversation, isPending } = useCreateConversation();

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);

    const q = formData.get("q")?.toString();
    createConversation({ q });
  };

  return (
    <div className="flex flex-col gap-1 w-full">
      <form
        ref={ref}
        onSubmit={handleSubmit}
        className="flex flex-col items-center gap-2"
      >
        <div
          className={cn(
            "px-4 rounded-lg text-[17px] leading-5 w-full transition-colors duration-200",
            inputIsFocused ? "bg-[#171717]" : "bg-[#171717]",
          )}
        >
          {isPending ? (
            <div className="flex justify-center py-[17px]">
              <LoadingSpinner size="small" />
            </div>
          ) : (
            <div className="relative">
              <ChatInput
                name="q"
                onSubmit={() => {
                  if (typeof ref !== "function") ref?.current?.requestSubmit();
                }}
                onChange={(message) => setText(message)}
                onFocus={() => setInputIsFocused(true)}
                onBlur={() => setInputIsFocused(false)}
                onImagePaste={async (imageFiles) => {
                  const promises = imageFiles.map(convertImageToBase64);
                  const base64Images = await Promise.all(promises);
                  base64Images.forEach((base64) => {
                    dispatch(addFile(base64));
                  });
                }}
                value={text}
                maxRows={15}
                showButton={!!text}
                className="text-[17px] leading-5 py-[17px] pl-7 bg-[#171717]"
                buttonClassName="pb-[7px]"
                disabled={navigation.state === "submitting"}
              />
              <div className="absolute left-[-7px] top-1/2 -translate-y-1/2">
                <UploadImageInput
                  onUpload={async (uploadedFiles) => {
                    const promises = uploadedFiles.map(convertImageToBase64);
                    const base64Images = await Promise.all(promises);
                    base64Images.forEach((base64) => {
                      dispatch(addFile(base64));
                    });
                  }}
                  label={<AttachImageLabel />}
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
  );
}
