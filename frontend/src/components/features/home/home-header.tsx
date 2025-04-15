import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { BrandButton } from "../settings/brand-button";
import AllHandsLogo from "#/icons/hands.svg?react";

export function HomeHeader() {
  const {
    mutate: createConversation,
    isPending,
    isSuccess,
  } = useCreateConversation();
  const isCreatingConversationElsewhere = useIsCreatingConversation();

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  return (
    <header className="flex justify-between items-end">
      <section className="flex flex-col gap-5">
        <AllHandsLogo />
        <h1 className="heading">Let&apos;s Start Building!</h1>
        <p className="text-sm max-w-[424px]">
          OpenHands makes it easy to build and maintain software using AI-driven
          development.
        </p>
      </section>

      <section className="flex flex-col gap-4">
        <BrandButton
          testId="header-launch-button"
          variant="primary"
          type="button"
          className="w-full"
          onClick={() => createConversation({})}
          isDisabled={isCreatingConversation}
        >
          {!isCreatingConversation && "Launch from Scratch"}
          {isCreatingConversation && "Loading..."}
        </BrandButton>
        <p className="text-sm">
          Not sure how to start?{" "}
          <a
            href="https://docs.all-hands.dev/modules/usage/getting-started"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2"
          >
            Read this
          </a>
        </p>
      </section>
    </header>
  );
}
