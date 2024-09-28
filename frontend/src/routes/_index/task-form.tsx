import React from "react";
import { Form, useFetcher, useNavigation } from "@remix-run/react";
import { useDispatch, useSelector } from "react-redux";
import Send from "#/assets/send.svg?react";
import Clip from "#/assets/clip.svg?react";
import { cn } from "#/utils/utils";
import { RootState } from "#/store";
import { removeFile } from "#/state/initial-query-slice";
import { SuggestionBubble } from "#/components/suggestion-bubble";
import { SUGGESTIONS } from "#/utils/suggestions";

interface MainTextareaInputProps {
  placeholder: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  formRef: React.RefObject<HTMLFormElement>;
}

function MainTextareaInput({
  placeholder,
  value,
  onChange,
  formRef,
}: MainTextareaInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const adjustHeight = () => {
    const MAX_LINES = 15;

    const textarea = textareaRef.current;
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
      ref={textareaRef}
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
        "bg-[#404040] placeholder:text-[#A3A3A3] border border-[#525252] w-[600px] rounded-lg px-[16px] py-[18px] text-[17px] leading-5",
        "focus:bg-[#525252]",
        "resize-none",
      )}
    />
  );
}

const getRandomKey = (obj: Record<string, string>) => {
  const keys = Object.keys(obj);
  const randomKey = keys[Math.floor(Math.random() * keys.length)];

  return randomKey;
};

interface UploadedFilePreviewProps {
  file: string; // base64
  onRemove: () => void;
}

function UploadedFilePreview({ file, onRemove }: UploadedFilePreviewProps) {
  return (
    <div className="relative">
      <button
        type="button"
        aria-label="Remove"
        onClick={onRemove}
        className="absolute right-1 top-1 text-[#A3A3A3] hover:text-danger"
      >
        &times;
      </button>
      <img src={file} alt="" className="w-16 h-16 aspect-auto rounded" />
    </div>
  );
}

interface TaskFormProps {
  importedProjectZip: File | null;
}

export function TaskForm({ importedProjectZip }: TaskFormProps) {
  const dispatch = useDispatch();
  const navigation = useNavigation();
  const fetcher = useFetcher();

  const { files, selectedRepository } = useSelector(
    (state: RootState) => state.initalQuery,
  );

  const formRef = React.useRef<HTMLFormElement>(null);
  const [text, setText] = React.useState("");
  const [suggestion, setSuggestion] = React.useState(
    getRandomKey(
      selectedRepository ? SUGGESTIONS.repo : SUGGESTIONS["non-repo"],
    ),
  );

  React.useEffect(() => {
    // Display a suggestion based on whether a repository is selected
    if (selectedRepository) {
      setSuggestion(getRandomKey(SUGGESTIONS.repo));
    } else {
      setSuggestion(getRandomKey(SUGGESTIONS["non-repo"]));
    }
  }, [selectedRepository]);

  const onRefreshSuggestion = () => {
    const suggestions = SUGGESTIONS[selectedRepository ? "repo" : "non-repo"];
    // remove current suggestion to avoid refreshing to the same suggestion
    const suggestionCopy = { ...suggestions };
    delete suggestionCopy[suggestion];

    const key = getRandomKey(suggestionCopy);
    setSuggestion(key);
  };

  const onClickSuggestion = () => {
    const suggestions = SUGGESTIONS[selectedRepository ? "repo" : "non-repo"];
    const value = suggestions[suggestion];
    setText(value);
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
  };

  const handleSubmitForm = () => {
    // This is submitted on top of the form submission
    const formData = new FormData();
    if (importedProjectZip) {
      formData.append("imported-project", importedProjectZip);
      fetcher.submit(formData, {
        method: "POST",
        action: "/upload-initial-files",
        encType: "multipart/form-data",
      });
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {files.length > 0 && (
        <div className="flex gap-2">
          {files.map((file, index) => (
            <UploadedFilePreview
              key={index}
              file={file}
              onRemove={() => dispatch(removeFile(file))}
            />
          ))}
        </div>
      )}
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
        <div className="relative">
          <MainTextareaInput
            placeholder={
              selectedRepository
                ? `What would you like to change in ${selectedRepository}`
                : "What do you want to build?"
            }
            onChange={handleChange}
            value={text}
            formRef={formRef}
          />
          {!!text && (
            <button
              type="submit"
              aria-label="Submit"
              className="absolute right-4 top-1/2 transform -translate-y-1/2"
              disabled={navigation.state === "loading"}
            >
              <Send width={24} height={24} />
            </button>
          )}
        </div>
      </Form>
      <label className="flex self-start items-center text-[#A3A3A3] text-xs leading-[18px] -tracking-[0.08px]">
        <Clip width={16} height={16} />
        Attach a file
        <input
          hidden
          type="file"
          accept="image/*"
          id="file-input"
          multiple
          onChange={(event) => {
            // CURRENTLY ONLY SUPPORTS SINGLE FILE UPLOAD
            if (event.target.files) {
              const formData = new FormData();
              formData.append("file", event.target.files[0]);

              fetcher.submit(formData, {
                method: "POST",
                action: "/upload-initial-files",
                encType: "multipart/form-data",
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
