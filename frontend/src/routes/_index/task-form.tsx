import React from "react";
import { Form, useFetcher, useNavigation } from "@remix-run/react";
import { useDispatch, useSelector } from "react-redux";
import Send from "#/assets/send.svg?react";
import Clip from "#/assets/clip.svg?react";
import { cn } from "#/utils/utils";
import { RootState } from "#/store";
import { removeFile } from "#/state/initial-query-slice";

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

export function TaskForm() {
  const dispatch = useDispatch();
  const navigation = useNavigation();
  const fetcher = useFetcher();

  const { files } = useSelector((state: RootState) => state.initalQuery);

  const formRef = React.useRef<HTMLFormElement>(null);
  const [hasText, setHasText] = React.useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setHasText(!!e.target.value);
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
      <Form ref={formRef} method="post" className="relative">
        <input
          name="q"
          type="text"
          placeholder="What do you want to build?"
          onChange={handleChange}
          className={cn(
            "bg-[#404040] placeholder:text-[#A3A3A3] border border-[#525252] w-[600px] rounded-lg px-[16px] py-[18px] text-[17px] leading-5",
            "focus:bg-[#525252]",
          )}
        />
        {hasText && (
          <button
            type="submit"
            aria-label="Submit"
            className="absolute right-4 top-1/2 transform -translate-y-1/2"
            disabled={navigation.state === "loading"}
          >
            <Send width={24} height={24} />
          </button>
        )}
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
