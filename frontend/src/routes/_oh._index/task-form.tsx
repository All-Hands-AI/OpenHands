import React from "react";
import { Form, useNavigation } from "@remix-run/react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "#/store";
import { addFile, removeFile } from "#/state/initial-query-slice";
import { SuggestionBubble } from "#/components/suggestion-bubble";
import { SUGGESTIONS } from "#/utils/suggestions";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { ChatInput } from "#/components/chat-input";
import { UploadImageInput } from "#/components/upload-image-input";
import { ImageCarousel } from "#/components/image-carousel";
import { getRandomKey } from "#/utils/get-random-key";
import { AttachImageLabel } from "#/components/attach-image-label";
import { cn } from "#/utils/utils";

export function TaskForm() {
  const dispatch = useDispatch();
  const navigation = useNavigation();

  const { selectedRepository, files } = useSelector(
    (state: RootState) => state.initalQuery,
  );

  const formRef = React.useRef<HTMLFormElement>(null);
  const [text, setText] = React.useState("");
  const [suggestion, setSuggestion] = React.useState(
    getRandomKey(SUGGESTIONS["non-repo"]),
  );
  const [inputIsFocused, setInputIsFocused] = React.useState(false);

  const onRefreshSuggestion = () => {
    const suggestions = SUGGESTIONS["non-repo"];
    // remove current suggestion to avoid refreshing to the same suggestion
    const suggestionCopy = { ...suggestions };
    delete suggestionCopy[suggestion];

    const key = getRandomKey(suggestionCopy);
    setSuggestion(key);
  };

  const onClickSuggestion = () => {
    const suggestions = SUGGESTIONS["non-repo"];
    const value = suggestions[suggestion];
    setText(value);
  };

  const placeholder = React.useMemo(() => {
    if (selectedRepository) {
      return `What would you like to change in ${selectedRepository}?`;
    }

    return "What do you want to build?";
  }, [selectedRepository]);

  return (
    <div className="flex flex-col gap-2 w-full">
      <Form
        ref={formRef}
        method="post"
        className="flex flex-col items-center gap-2"
        replace
      >
        <SuggestionBubble
          suggestion={suggestion}
          onClick={onClickSuggestion}
          onRefresh={onRefreshSuggestion}
        />
        <div
          className={cn(
            "border border-neutral-600 px-4 py-[17px] rounded-lg text-[17px] leading-5 w-full transition-colors duration-200",
            inputIsFocused ? "bg-neutral-600" : "bg-neutral-700",
            "hover:border-neutral-500 focus-within:border-neutral-500",
          )}
        >
          <ChatInput
            name="q"
            onSubmit={() => {
              formRef.current?.requestSubmit();
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
            placeholder={placeholder}
            value={text}
            maxRows={15}
            showButton={!!text}
            className="text-[17px] leading-5"
            disabled={navigation.state === "submitting"}
          />
        </div>
      </Form>
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
