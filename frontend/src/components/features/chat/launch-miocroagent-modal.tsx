import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";
import React from "react";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";
import { SettingsInput } from "../settings/settings-input";
import { MemoryService } from "#/api/memory-service/memory-service.api";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";
import { FileService } from "#/api/file-service/file-service.api";
import { BadgeInput } from "#/components/shared/inputs/badge-input";

interface LaunchMicroagentModalProps {
  onClose: () => void;
  onLaunch: () => void;
}

export function LaunchMicroagentModal({
  onClose,
  onLaunch,
}: LaunchMicroagentModalProps) {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { data: prompt } = useQuery({
    queryKey: ["memory", "prompt", conversationId],
    queryFn: () => MemoryService.getPrompt(conversationId!),
    enabled: !!conversationId,
  });
  const { data: microagents } = useQuery({
    queryKey: ["files", "microagents", conversationId],
    queryFn: () => FileService.getFiles(conversationId!, ".openhands"),
    enabled: !!conversationId,
  });

  const [badges, setBadges] = React.useState<string[]>([]);

  const formAction = (formData: FormData) => {
    // console.log(Object.fromEntries(formData.entries()));
  };

  return (
    <ModalBackdrop>
      <ModalBody className="items-start">
        <h2 className="font-bold text-[20px] leading-6 -tracking-[0.01em]">
          Add to Microagent
        </h2>

        <form
          data-testid="launch-microagent-modal"
          action={formAction}
          className="flex flex-col gap-6"
        >
          <SettingsInput
            type="text"
            testId="description-input"
            name="description-input"
            label="What would you like to add to the Microagent?"
            defaultValue={prompt}
          />

          <SettingsDropdownInput
            testId="target-input"
            name="target-input"
            label="Where should we put it?"
            items={
              microagents?.map((item) => ({
                key: item,
                label: item,
              })) || []
            }
          />

          <label
            htmlFor="trigger-input"
            className="flex flex-col gap-2.5 w-fit"
          >
            Add a trigger for the microagent
            <BadgeInput
              name="trigger-input"
              value={badges}
              onChange={setBadges}
            />
          </label>

          <div className="flex items-center justify-end gap-2">
            <BrandButton type="button" variant="secondary" onClick={onClose}>
              Cancel
            </BrandButton>
            <BrandButton type="submit" variant="primary" onClick={onLaunch}>
              Launch
            </BrandButton>
          </div>
        </form>
      </ModalBody>
    </ModalBackdrop>
  );
}
