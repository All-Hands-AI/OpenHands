import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";
import React from "react";
import { FaCircleInfo } from "react-icons/fa6";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";
import { MemoryService } from "#/api/memory-service/memory-service.api";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";
import { FileService } from "#/api/file-service/file-service.api";
import { BadgeInput } from "#/components/shared/inputs/badge-input";
import { cn } from "#/utils/utils";
import CloseIcon from "#/icons/close.svg?react";

interface LaunchMicroagentModalProps {
  onClose: () => void;
  onLaunch: (query: string, target: string, triggers: string[]) => void;
  eventId: number;
  selectedRepo?: string | null;
  isLoading: boolean;
}

export function LaunchMicroagentModal({
  onClose,
  onLaunch,
  eventId,
  selectedRepo,
  isLoading,
}: LaunchMicroagentModalProps) {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { data: prompt, isLoading: promptIsLoading } = useQuery({
    queryKey: ["memory", "prompt", conversationId, eventId],
    queryFn: () => MemoryService.getPrompt(conversationId!, eventId),
    enabled: !!conversationId,
  });

  const microagentPath = selectedRepo
    ? `${selectedRepo}/.openhands/microagents/`
    : ".openhands/microagents/";
  const { data: microagents } = useQuery({
    queryKey: ["files", "microagents", conversationId, microagentPath],
    queryFn: () => FileService.getFiles(conversationId!, microagentPath),
    enabled: !!conversationId,
    select: (data) =>
      data.map((fileName) => fileName.replace(microagentPath, "")),
  });

  const [triggers, setTriggers] = React.useState<string[]>([]);

  const formAction = (formData: FormData) => {
    const query = formData.get("query-input")?.toString();
    const target = formData.get("target-input")?.toString();

    if (query && target) {
      onLaunch(query, target, triggers);
    }
  };

  return (
    <ModalBackdrop>
      <ModalBody className="items-start w-[728px]">
        <div className="flex items-center justify-between w-full">
          <h2 className="font-bold text-[20px] leading-6 -tracking-[0.01em] flex items-center gap-2">
            Add to Microagent
            <a
              href="https://docs.all-hands.dev/usage/prompting/microagents-overview#microagents-overview"
              target="_blank"
              rel="noopener noreferrer"
            >
              <FaCircleInfo className="text-primary" />
            </a>
          </h2>

          <button type="button" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <form
          data-testid="launch-microagent-modal"
          action={formAction}
          className="flex flex-col gap-6 w-full"
        >
          <label
            htmlFor="query-input"
            className="flex flex-col gap-2.5 w-full text-sm"
          >
            What would you like to add to the Microagent?
            <textarea
              required
              data-testid="query-input"
              name="query-input"
              defaultValue={prompt}
              placeholder="Describe what you want to add to the Microagent..."
              rows={6}
              className={cn(
                "bg-tertiary border border-[#717888] w-full rounded p-2 placeholder:italic placeholder:text-tertiary-alt resize-none",
                "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
              )}
            />
          </label>

          <SettingsDropdownInput
            testId="target-input"
            name="target-input"
            label="Where should we put it?"
            placeholder="Select a microagent file or enter a custom value"
            required
            allowsCustomValue
            items={
              microagents?.map((item) => ({
                key: item,
                label: item,
              })) || []
            }
          />

          <label
            htmlFor="trigger-input"
            className="flex flex-col gap-2.5 w-full text-sm"
          >
            Add a trigger for the microagent
            <BadgeInput
              name="trigger-input"
              value={triggers}
              placeholder="Type a trigger and press Space to add it"
              onChange={setTriggers}
            />
          </label>

          <div className="flex items-center justify-end gap-2">
            <BrandButton type="button" variant="secondary" onClick={onClose}>
              Cancel
            </BrandButton>
            <BrandButton
              type="submit"
              variant="primary"
              isDisabled={isLoading || promptIsLoading}
            >
              Launch
            </BrandButton>
          </div>
        </form>
      </ModalBody>
    </ModalBackdrop>
  );
}
