import React from "react";
import { Form, useNavigation } from "@remix-run/react";
import { useDispatch, useSelector } from "react-redux";
import Clip from "#/assets/clip.svg?react";
import { cn } from "#/utils/utils";
import { RootState } from "#/store";
import { addFile, setImportedProjectZip } from "#/state/initial-query-slice";
import { SuggestionBubble } from "#/components/suggestion-bubble";
import { SUGGESTIONS } from "#/utils/suggestions";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { ChatInput } from "#/components/chat-input";

const convertZipToBase64 = async (file: File) => {
  const reader = new FileReader();

  return new Promise<string>((resolve) => {
    reader.onload = () => {
      resolve(reader.result as string);
    };
    reader.readAsDataURL(file);
  });
};

interface MainTextareaInputProps {
  disabled: boolean;
  placeholder: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  formRef: React.RefObject<HTMLFormElement>;
}

const MainTextareaInput = React.forwardRef<
  HTMLTextAreaElement,
  MainTextareaInputProps
>(({ disabled, placeholder, value, onChange, formRef }, ref) => {
  const adjustHeight = () => {
    const MAX_LINES = 15;

    // ref can either be a callback ref or a MutableRefObject
    const textarea = typeof ref === "function" ? null : ref?.current;
    if (textarea) {
      textarea.style.height = "auto"; // Reset to auto to recalculate scroll height
      const { scrollHeight } = textarea;

      // Calculate based on line height and max lines
      const lineHeight = parseInt(
        window.getComputedStyle(textarea).lineHeight,
        10,
      );
      const maxHeight = lineHeight * MAX_LINES;

      textarea.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  };

  React.useEffect(() => {
    adjustHeight();
  }, [value]);

  return (
    <textarea
      ref={ref}
      disabled={disabled}
      name="q"
      rows={1}
      placeholder={placeholder}
      onChange={onChange}
      onKeyDown={(e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          formRef.current?.requestSubmit();
        }
      }}
      value={value}
      className={cn(
        "bg-[#404040] placeholder:text-[#A3A3A3] border border-[#525252] w-full rounded-lg px-4 py-[18px] text-[17px] leading-5",
        "pr-[calc(16px+24px)]", // 24px for the send button
        "focus:bg-[#525252]",
        "resize-none",
      )}
    />
  );
});

MainTextareaInput.displayName = "MainTextareaInput";

const getRandomKey = (obj: Record<string, string>) => {
  const keys = Object.keys(obj);
  const randomKey = keys[Math.floor(Math.random() * keys.length)];

  return randomKey;
};

interface TaskFormProps {
  importedProjectZip: File | null;
  textareaRef?: React.RefObject<HTMLTextAreaElement>;
}

export function TaskForm({ importedProjectZip, textareaRef }: TaskFormProps) {
  const dispatch = useDispatch();
  const navigation = useNavigation();

  const { selectedRepository } = useSelector(
    (state: RootState) => state.initalQuery,
  );

  const hasLoadedProject = React.useMemo(
    () => importedProjectZip || selectedRepository,
    [importedProjectZip, selectedRepository],
  );

  const formRef = React.useRef<HTMLFormElement>(null);
  const [text, setText] = React.useState("");
  const [suggestion, setSuggestion] = React.useState(
    getRandomKey(hasLoadedProject ? SUGGESTIONS.repo : SUGGESTIONS["non-repo"]),
  );

  React.useEffect(() => {
    // Display a suggestion based on whether a repository is selected
    if (hasLoadedProject) {
      setSuggestion(getRandomKey(SUGGESTIONS.repo));
    } else {
      setSuggestion(getRandomKey(SUGGESTIONS["non-repo"]));
    }
  }, [selectedRepository, importedProjectZip]);

  const onRefreshSuggestion = () => {
    const suggestions = SUGGESTIONS[hasLoadedProject ? "repo" : "non-repo"];
    // remove current suggestion to avoid refreshing to the same suggestion
    const suggestionCopy = { ...suggestions };
    delete suggestionCopy[suggestion];

    const key = getRandomKey(suggestionCopy);
    setSuggestion(key);
  };

  const onClickSuggestion = () => {
    const suggestions = SUGGESTIONS[hasLoadedProject ? "repo" : "non-repo"];
    const value = suggestions[suggestion];
    setText(value);
  };

  const handleSubmitForm = async () => {
    // This is handled on top of the form submission
    if (importedProjectZip) {
      dispatch(
        setImportedProjectZip(await convertZipToBase64(importedProjectZip)),
      );
    }
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
        onSubmit={handleSubmitForm}
        replace
      >
        <SuggestionBubble
          suggestion={suggestion}
          onClick={onClickSuggestion}
          onRefresh={onRefreshSuggestion}
        />
        <div className="bg-neutral-700 border border-neutral-600 px-4 py-[17px] rounded-lg text-[17px] leading-5 w-full">
          <ChatInput
            name="q"
            onSubmit={() => {
              formRef.current?.requestSubmit();
            }}
            onChange={(message) => setText(message)}
            placeholder={placeholder}
            value={text}
            maxRows={15}
            showSubmitButton={!!text}
            className="text-[17px] leading-5"
            disabled={navigation.state === "submitting"}
          />
        </div>
      </Form>
      <label className="flex self-start items-center text-[#A3A3A3] text-xs leading-[18px] -tracking-[0.08px] cursor-pointer">
        <Clip width={16} height={16} />
        Attach images
        <input
          hidden
          type="file"
          accept="image/*"
          id="file-input"
          multiple
          onChange={(event) => {
            if (event.target.files) {
              Array.from(event.target.files).forEach((file) => {
                convertImageToBase64(file).then((base64) => {
                  dispatch(addFile(base64));
                });
              });
            } else {
              // TODO: handle error
            }
          }}
        />
      </label>
    </div>
  );
}
