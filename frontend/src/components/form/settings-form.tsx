import {
  Autocomplete,
  AutocompleteItem,
  Input,
  Switch,
} from "@nextui-org/react";
import React, { Suspense } from "react";
import clsx from "clsx";
import { Await, useFetcher } from "@remix-run/react";
import { organizeModelsAndProviders } from "#/utils/organizeModelsAndProviders";
import { ModelSelector } from "#/components/modals/settings/ModelSelector";
import { Settings } from "#/services/settings";
import ConfirmResetDefaultsModal from "#/components/modals/confirmation-modals/ConfirmResetDefaultsModal";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";

interface SettingsFormProps {
  settings: Settings;
  models: Promise<string[]>;
  agents: Promise<string[]>;
  onClose: () => void;
}

export function SettingsForm({
  settings,
  models,
  agents,
  onClose,
}: SettingsFormProps) {
  const fetcher = useFetcher();
  const formRef = React.useRef<HTMLFormElement>(null);
  const [isCustomModel, setIsCustomModel] = React.useState(false);
  const [confirmResetDefaultsModalOpen, setConfirmResetDefaultsModalOpen] =
    React.useState(false);

  return (
    <fetcher.Form
      ref={formRef}
      data-testid="settings-form"
      method="POST"
      action="/settings"
      className="flex flex-col gap-6"
      onSubmit={onClose}
    >
      <div className="flex flex-col gap-2">
        <Switch
          name="use-custom-model"
          data-testid="custom-model-toggle"
          isSelected={isCustomModel}
          onValueChange={setIsCustomModel}
          classNames={{
            thumb: clsx(
              "bg-[#5D5D5D] w-3 h-3",
              "group-data-[selected=true]:bg-white",
            ),
            wrapper: clsx(
              "border border-[#D4D4D4] bg-white px-[6px] w-12 h-6",
              "group-data-[selected=true]:border-transparent group-data-[selected=true]:bg-[#4465DB]",
            ),
            label: "text-[#A3A3A3] text-xs",
          }}
        >
          Use custom model
        </Switch>

        {isCustomModel && (
          <fieldset
            data-testid="custom-model-input"
            className="flex flex-col gap-2"
          >
            <label
              htmlFor="custom-model"
              className="font-[500] text-[#A3A3A3] text-xs"
            >
              Custom Model
            </label>
            <Input
              id="custom-model"
              name="custom-model"
              aria-label="Custom Model"
              classNames={{
                inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
              }}
            />
          </fieldset>
        )}

        {!isCustomModel && (
          <Suspense fallback={<div>Loading models...</div>}>
            <Await resolve={models}>
              {(resolvedModels) => (
                <ModelSelector
                  models={organizeModelsAndProviders(resolvedModels)}
                  currentModel={settings.LLM_MODEL}
                />
              )}
            </Await>
          </Suspense>
        )}

        <fieldset data-testid="api-key-input" className="flex flex-col gap-2">
          <label
            htmlFor="api-key"
            className="font-[500] text-[#A3A3A3] text-xs"
          >
            API Key
          </label>
          <Input
            id="api-key"
            name="api-key"
            aria-label="API Key"
            type="password"
            defaultValue={settings.LLM_API_KEY}
            classNames={{
              inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
            }}
          />
          <p className="text-sm text-[#A3A3A3]">
            Don&apos;t know your API key?{" "}
            <span className="underline underline-offset-2">
              Click here for instructions
            </span>
          </p>
        </fieldset>

        <fieldset data-testid="agent-selector" className="flex flex-col gap-2">
          <label htmlFor="agent" className="font-[500] text-[#A3A3A3] text-xs">
            Agent
          </label>
          <Suspense fallback={<div>Loading...</div>}>
            <Await resolve={agents}>
              {(resolvedAgents) => (
                <Autocomplete
                  isRequired
                  id="agent"
                  aria-label="Agent"
                  data-testid="agent-input"
                  name="agent"
                  defaultSelectedKey={settings.AGENT}
                  isClearable={false}
                  inputProps={{
                    classNames: {
                      inputWrapper:
                        "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
                    },
                  }}
                >
                  {resolvedAgents.map((agent) => (
                    <AutocompleteItem key={agent} value={agent}>
                      {agent}
                    </AutocompleteItem>
                  ))}
                </Autocomplete>
              )}
            </Await>
          </Suspense>
        </fieldset>
      </div>

      <div className="flex flex-col gap-2">
        <button
          type="submit"
          className="bg-[#4465DB] text-sm font-[500] py-[10px] rounded"
        >
          Save
        </button>
        <button
          type="button"
          data-testid="close-button"
          className="bg-[#737373] text-sm font-[500] py-[10px] rounded"
          onClick={onClose}
        >
          Close
        </button>
        <button
          type="button"
          onClick={() => {
            setConfirmResetDefaultsModalOpen(true);
          }}
          className="text-sm text-[#EF3744] self-start"
        >
          Reset to defaults
        </button>
      </div>
      {confirmResetDefaultsModalOpen && (
        <ModalBackdrop>
          <ConfirmResetDefaultsModal
            onConfirm={() => {
              const formData = new FormData(formRef.current ?? undefined);
              formData.set("intent", "reset");
              fetcher.submit(formData, { method: "POST", action: "/settings" });

              onClose();
            }}
            onCancel={() => setConfirmResetDefaultsModalOpen(false)}
          />
        </ModalBackdrop>
      )}
    </fetcher.Form>
  );
}
