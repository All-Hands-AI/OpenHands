import { SuggestionBox } from "./suggestion-box";

interface ImportProjectSuggestionBoxProps {
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function ImportProjectSuggestionBox({
  onChange,
}: ImportProjectSuggestionBoxProps) {
  return (
    <SuggestionBox
      title="+ Import Project"
      content={
        <label htmlFor="import-project" className="w-full flex justify-center">
          <span className="border-2 border-dashed border-neutral-600 rounded px-2 py-1 cursor-pointer">
            Upload a .zip
          </span>
          <input
            hidden
            type="file"
            accept="application/zip"
            id="import-project"
            multiple={false}
            onChange={onChange}
          />
        </label>
      }
    />
  );
}
